"""
漢字抜け熟語パズルを1問生成する処理。generate.py から generate_puzzle を呼び出して使う。

【用語】
    番号: 空欄にした漢字に付ける番号。漢字と番号は一対一で、同じ漢字は問題内のどこに出ても同じ番号の空欄になる
    親: 子をつなげる元になる空欄の漢字
    子: 親の漢字を含む熟語。1つの親につなげる子のまとまりをグループと呼ぶ
    順番待ち: まだ子をつなげていない空欄の漢字の列。古い順に取り出して親にする

【生成の流れ】
    1. 起点の熟語をランダムに1語選ぶ。各文字を ADDITIONAL_BLANK_PROBABILITY の確率で空欄にし、
       1文字も空欄にならなければ1文字だけ空欄にする
    2. 語数に達するか順番待ちがなくなるまで、順番待ちから親を1つ取り出して子をつなげる
       a. 子の候補：親の漢字を含み、まだ問題に入っていない熟語
          no_shared_pair のときは、問題に入った熟語と同じ2文字の並びを持つ熟語も外す
       b. 候補がなければ、その親からは子をつなげない
       c. 子の数を CHILD_COUNT_WEIGHTS の確率で決める
          親を作った子が1個だけだった場合は FORCED_CHILD_COUNT 個にする
          どちらも、残りの語数と候補の数を超えない（足りなければ選べるだけ選ぶ）
       d. 子を1個ずつランダムに選ぶ。no_shared_pair のときは、選ぶたびに、
          選んだ子と同じ2文字の並びを持つ候補を外してから次を選ぶ
          選べた子が1個で、その子の文字がすべて親の漢字か番号付きの漢字だった場合は、
          そのような熟語を候補から外して選び直す（新しい空欄を作れない子だけで枝が止まるのを防ぐ）
       e. 子の空欄を決める（decide_group_blanks）
       f. 子を問題に登録する。新しく空欄にした漢字が、先に入った熟語に見える文字として出ていたら、
          その文字もさかのぼって同じ番号の空欄にする
    3. 順番待ちがなくなっても語数に届かなければ、バックトラックする（backtrack）
    4. 語数に達したら、1語にしか出てこない番号を見える文字に戻し、番号を1から振り直す
    5. 同じ漢字が、ある場所では空欄、別の場所では見える文字になっていないかを確かめる

【バックトラック】
    直前の親（最後に子をつなげた親）から、次の順にやり直す
    段階1: 子はそのままで、空欄の付け方を変える（前に試した付け方は使わない）
           MAX_BLANK_TRIES 回まで（最初の1回を含む）。試していない付け方がなければすぐ段階2へ
    段階2: 子を選び直す（子の数も抽選し直す。前に選んだ子がまた選ばれてもよい）
           選び直すたびに段階1も行う。MAX_CHILD_TRIES 回まで（最初の1回を含む）
    段階3: その親の漢字を空欄にした熟語のグループ（1つ上の親）に戻り、段階1からやり直す
           戻るときは、そのグループより後に行った処理をすべて取り消す
           戻った親の回数は数え直す
           起点の熟語まで戻った場合は、起点の熟語はそのままで空欄の付け方を変える
           （前に試した付け方は使わない。MAX_BLANK_TRIES 回まで）
    やり直しの回数（空欄の付け直し・子の選び直し）は1問で MAX_TOTAL_RETRIES 回まで
    これを超えるか、起点の熟語で試せる付け方がなくなったら、その問題は失敗とする
"""

import math
import random
from collections import defaultdict, deque

# ==== パラメータ ====
ADDITIONAL_BLANK_PROBABILITY = 0.4                # 残り文字1つごとに独立適用
CHILD_COUNT_WEIGHTS = {2: 0.5, 3: 0.3, 4: 0.2}    # 1つの親から選ぶ子の数とその確率
FORCED_CHILD_COUNT = 4                            # 子が1個しか選べなかった場合、その子が作った空欄から選ぶ子の数
MAX_BLANK_TRIES = 5                               # 段階1：同じ子のまま空欄の付け方を試す回数
MAX_CHILD_TRIES = 5                               # 段階2：1つの親で子を選ぶ回数
MAX_TOTAL_RETRIES = 100                           # 1問でやり直す回数の合計
MAX_PATTERN_DRAWS = 50                            # まだ試していない空欄の付け方を探すときの抽選回数（これで見つからなければ、試せる付け方はないとみなす）

START = "start"   # 起点の熟語が作った番号の作り手を表す印


def build_graph(words):
    """漢字 -> 熟語リスト、の対応表を構築する"""
    kanji_to_words = defaultdict(list)
    for word in words:
        for k in set(word):  # 同じ漢字が複数回出る熟語でも重複登録しない
            kanji_to_words[k].append(word)
    return kanji_to_words


def char_pairs(word):
    """熟語に含まれる、連続した2文字の並びの集合を返す（例：裁判所 -> {裁判, 判所}）"""
    return {word[i:i + 2] for i in range(len(word) - 1)}


def decide_child_count():
    """1つの親から選ぶ子の数を、CHILD_COUNT_WEIGHTS の確率で決める"""
    counts = list(CHILD_COUNT_WEIGHTS.keys())
    weights = list(CHILD_COUNT_WEIGHTS.values())
    return random.choices(counts, weights=weights)[0]


class State:
    """生成中の状態。バックトラックのために丸ごと複製できるようにしている"""

    def __init__(self):
        self.used_words = []        # 問題に入った熟語（入った順）
        self.puzzle_words = []      # [{"word": 熟語, "blanks": {位置: (漢字, 番号)}}, ...]
        self.kanji_number = {}      # 漢字 -> 番号
        self.kanji_creator = {}     # 漢字 -> その漢字に番号を付けたグループ（起点の熟語なら START）
        self.used_pairs = set()     # 問題に入った熟語の2文字の並び
        self.frontier = deque()     # 順番待ち。要素は (漢字, 子を FORCED_CHILD_COUNT 個選ぶかどうか)
        self.next_number = 1
        self.skip_count = 0         # 候補がなくて子をつなげなかった親の数

    def copy(self):
        new = State()
        new.used_words = list(self.used_words)
        new.puzzle_words = [{"word": e["word"], "blanks": dict(e["blanks"])} for e in self.puzzle_words]
        new.kanji_number = dict(self.kanji_number)
        new.kanji_creator = dict(self.kanji_creator)
        new.used_pairs = set(self.used_pairs)
        new.frontier = deque(self.frontier)
        new.next_number = self.next_number
        new.skip_count = self.skip_count
        return new


class Group:
    """1つの親につなげた子のグループ。バックトラックでやり直すための情報を持つ"""

    def __init__(self, before, parent, force_four, creator, candidates):
        self.before = before            # 子を登録する前の状態（親は順番待ちから取り出し済み）
        self.parent = parent            # 親の漢字
        self.force_four = force_four    # 子を FORCED_CHILD_COUNT 個選ぶ親かどうか
        self.creator = creator          # 親の漢字に番号を付けたグループ（起点の熟語なら START）
        self.candidates = candidates    # 子の候補
        self.children = []
        self.pattern = None             # 今の空欄の付け方
        self.tried_patterns = set()     # 今の子で試した空欄の付け方
        self.blank_tries = 0
        self.child_tries = 0


def get_candidates(frontier_kanji, kanji_to_words, state, no_shared_pair):
    """
    frontier_kanji を含み、まだ問題に入っていない熟語を候補として返す。
    no_shared_pair のときは、問題に入った熟語と同じ2文字の並びを1つでも含む熟語も外す。
    """
    candidates = []
    for word in kanji_to_words.get(frontier_kanji, []):
        if word in state.used_words:
            continue
        if no_shared_pair and char_pairs(word) & state.used_pairs:
            continue
        candidates.append(word)
    return candidates


def is_all_numbered(word, parent, kanji_number):
    """熟語の文字が、すべて親の漢字か番号付きの漢字かどうか（新しい空欄もヒントも作れない熟語）"""
    return all(ch == parent or ch in kanji_number for ch in word)


def pick_sequential(candidates, wanted, no_shared_pair):
    """
    候補から子を最大 wanted 個選ぶ。
    no_shared_pair のときは1個ずつ選び、選ぶたびに、選んだ子と同じ2文字の並びを持つ候補を外す。
    """
    if not no_shared_pair:
        return random.sample(candidates, min(wanted, len(candidates)))
    picked = []
    pool = list(candidates)
    while pool and len(picked) < wanted:
        word = random.choice(pool)
        picked.append(word)
        pairs = char_pairs(word)
        pool = [c for c in pool if c != word and not (char_pairs(c) & pairs)]
    return picked


def pick_children(candidates, wanted, no_shared_pair, parent, kanji_number):
    """
    子を選ぶ。選べた子が1個で、その子が新しい空欄もヒントも作れない熟語だった場合は、
    そのような熟語を候補から外して選び直す。選べなければ空のリストを返す。
    """
    picked = pick_sequential(candidates, wanted, no_shared_pair)
    if len(picked) == 1 and is_all_numbered(picked[0], parent, kanji_number):
        usable = [c for c in candidates if not is_all_numbered(c, parent, kanji_number)]
        picked = pick_sequential(usable, wanted, no_shared_pair) if usable else []
    return picked


def decide_group_blanks(picked_words, frontier_kanji, kanji_number):
    """
    1つの親から選ばれた子のグループについて、各熟語の空欄の付け方を決める。

    各熟語の文字の扱い:
      - 親の漢字: 必ず空欄
      - 番号付きの漢字（親以外）: 必ず空欄。新しい空欄には数えない
      - それ以外の文字: ADDITIONAL_BLANK_PROBABILITY の確率で新しい空欄にする

    グループ単位で以下の2つを、できる範囲で保証する:
      - 新規空欄の最低保証: グループ内のどれか1つは必ず新しい空欄を持つ（つながりを止めない）
      - ヒントの保証: 子が2個以上のとき、半分以上（切り上げ）の熟語は見える漢字を1つ以上残す
        子が1個のときは新規空欄の保証を優先する

    戻り値: {熟語: 新しく空欄にする文字の集合}
    """
    assignments = {}
    for word in picked_words:
        free = sorted(set(word) - {frontier_kanji} - set(kanji_number))
        new_blanks = {c for c in free if random.random() < ADDITIONAL_BLANK_PROBABILITY}
        assignments[word] = [free, new_blanks]

    def total_new_blanks():
        return sum(len(b) for _, b in assignments.values())

    def has_hint(word):
        free, new_blanks = assignments[word]
        return len(new_blanks) < len(free)

    # ---- 新規空欄の最低保証 ----
    if total_new_blanks() == 0:
        words_with_free = [w for w in picked_words if assignments[w][0]]
        if words_with_free:
            word = random.choice(words_with_free)
            free, new_blanks = assignments[word]
            new_blanks.add(random.choice(free))

    # ---- ヒントの保証（子が2個以上のとき、半分以上） ----
    if len(picked_words) >= 2:
        required = math.ceil(len(picked_words) / 2)
        no_hint = [w for w in picked_words if not has_hint(w)]
        random.shuffle(no_hint)
        for word in no_hint:
            if sum(1 for w in picked_words if has_hint(w)) >= required:
                break
            free, new_blanks = assignments[word]
            if not new_blanks:
                continue  # 見える文字にできる文字がない熟語は対象外
            # 1文字外しても、グループ全体で新規空欄が0にならなければ外す
            if total_new_blanks() > 1:
                new_blanks.discard(random.choice(sorted(new_blanks)))

    return {word: frozenset(new_blanks) for word, (free, new_blanks) in assignments.items()}


def pattern_key(assignment):
    """空欄の付け方を、比べられる形にする"""
    return tuple(sorted((word, tuple(sorted(chars))) for word, chars in assignment.items()))


def draw_new_group_blanks(picked_words, frontier_kanji, kanji_number, tried_patterns):
    """まだ試していない空欄の付け方を抽選する。MAX_PATTERN_DRAWS 回で見つからなければ None"""
    for _ in range(MAX_PATTERN_DRAWS):
        assignment = decide_group_blanks(picked_words, frontier_kanji, kanji_number)
        if pattern_key(assignment) not in tried_patterns:
            return assignment
    return None


def draw_start_blanks(start_word):
    """起点の熟語の空欄にする文字を決める（各文字を確率で空欄にし、0文字なら1文字だけ空欄にする）"""
    chars = sorted(set(start_word))
    blanked = {c for c in chars if random.random() < ADDITIONAL_BLANK_PROBABILITY}
    if not blanked:
        blanked = {random.choice(chars)}
    return frozenset(blanked)


def draw_new_start_blanks(start_word, tried_patterns):
    """まだ試していない起点の熟語の空欄の付け方を抽選する。見つからなければ None"""
    for _ in range(MAX_PATTERN_DRAWS):
        blanked = draw_start_blanks(start_word)
        if blanked not in tried_patterns:
            return blanked
    return None


def register_word(state, word, blanked_chars, force_next, creator):
    """
    熟語を問題に登録する。
      - blanked_chars の漢字と、すでに番号付きの漢字を空欄にする
      - 新しく空欄にした漢字に番号を付け、順番待ちに積む
      - 新しく空欄にした漢字が、先に登録した熟語に見える文字として出ていたら、
        その文字も同じ番号の空欄にする（漢字と番号の一対一対応を保つため）
    """
    state.used_words.append(word)
    state.used_pairs.update(char_pairs(word))
    new_kanji = []
    for ch in word:
        if ch in blanked_chars and ch not in state.kanji_number:
            state.kanji_number[ch] = state.next_number
            state.kanji_creator[ch] = creator
            state.next_number += 1
            new_kanji.append(ch)
    for ch in new_kanji:
        state.frontier.append((ch, force_next))
        for entry in state.puzzle_words:
            for i, c in enumerate(entry["word"]):
                if c == ch:
                    entry["blanks"][i] = (ch, state.kanji_number[ch])
    blanks = {i: (ch, state.kanji_number[ch]) for i, ch in enumerate(word) if ch in state.kanji_number}
    state.puzzle_words.append({"word": word, "blanks": blanks})


def register_group(state, group, assignment):
    """グループの子をすべて登録する"""
    force_next = len(group.children) == 1   # 子が1個しか選べなかった場合、その子が作った空欄からは FORCED_CHILD_COUNT 個選ぶ
    for word in group.children:
        register_word(state, word, assignment[word] | {group.parent}, force_next, group)


def choose_count(group, state, target_word_count):
    """子の数を決める（残りの語数を超えない）"""
    wanted = FORCED_CHILD_COUNT if group.force_four else decide_child_count()
    return min(wanted, target_word_count - len(state.used_words))


def close_single_blanks(puzzle_words):
    """1語にしか出てこない番号を見える文字に戻し、残った番号を出てくる順に1から振り直す"""
    word_count_by_number = defaultdict(int)
    for entry in puzzle_words:
        for number in {number for _kanji, number in entry["blanks"].values()}:
            word_count_by_number[number] += 1
    for entry in puzzle_words:
        entry["blanks"] = {
            position: (kanji, number)
            for position, (kanji, number) in entry["blanks"].items()
            if word_count_by_number[number] >= 2
        }
    renumber = {}
    for entry in puzzle_words:
        for position in sorted(entry["blanks"]):
            kanji, number = entry["blanks"][position]
            if number not in renumber:
                renumber[number] = len(renumber) + 1
            entry["blanks"][position] = (kanji, renumber[number])


def is_consistent(puzzle_words):
    """同じ漢字が、ある場所では空欄、別の場所では見える文字になっていないか、番号と漢字が一対一かを確かめる"""
    blank_kanji = {}
    for entry in puzzle_words:
        for kanji, number in entry["blanks"].values():
            if blank_kanji.setdefault(kanji, number) != number:
                return False
    if len(set(blank_kanji.values())) != len(blank_kanji):
        return False
    for entry in puzzle_words:
        for i, ch in enumerate(entry["word"]):
            if ch in blank_kanji and i not in entry["blanks"]:
                return False
    return True


def generate_puzzle(words, target_word_count, seed=None, no_shared_pair=False):
    """
    1つのパズルを生成する。
    no_shared_pair が True のときは、同じ2文字の並びを持つ熟語を同じ問題に入れない
    （例：裁判所と裁判長、中学と中学校）。
    戻り値:
        puzzle_words: [{"word": str, "blanks": {index: (kanji, number)}}, ...]
        stats: {"reached": bool, "word_count": int, "skip_count": int, "retries": int,
                "start_word": str, "fail_reason": str or None}
    """
    if seed is not None:
        random.seed(seed)

    kanji_to_words = build_graph(words)

    # ---- 起点の熟語 ----
    start_word = random.choice(words)
    start_blanks = draw_start_blanks(start_word)
    start_tried = {start_blanks}
    start_tries = 1

    state = State()
    register_word(state, start_word, start_blanks, False, START)

    history = []    # これまでに子をつなげたグループ（古い順）
    retries = 0

    def fail(reason):
        stats = {
            "reached": False, "word_count": len(state.used_words), "skip_count": state.skip_count,
            "retries": retries, "start_word": start_word, "fail_reason": reason,
        }
        return state.puzzle_words, stats

    while True:
        # ---- 順番待ちから親を取り出して子をつなげる ----
        while len(state.used_words) < target_word_count and state.frontier:
            parent, force_four = state.frontier.popleft()
            candidates = get_candidates(parent, kanji_to_words, state, no_shared_pair)
            if not candidates:
                state.skip_count += 1
                continue
            group = Group(state.copy(), parent, force_four, state.kanji_creator[parent], candidates)
            group.children = pick_children(
                candidates, choose_count(group, state, target_word_count),
                no_shared_pair, parent, state.kanji_number
            )
            if not group.children:
                state.skip_count += 1
                continue
            assignment = decide_group_blanks(group.children, parent, state.kanji_number)
            group.pattern = pattern_key(assignment)
            group.tried_patterns = {group.pattern}
            group.blank_tries = 1
            group.child_tries = 1
            register_group(state, group, assignment)
            history.append(group)

        if len(state.used_words) >= target_word_count:
            break

        # ---- バックトラック ----
        while True:
            if retries >= MAX_TOTAL_RETRIES:
                return fail("やり直しの回数の上限")

            if not history:
                # 起点の熟語まで戻った：起点の熟語はそのままで、空欄の付け方を変える
                if start_tries >= MAX_BLANK_TRIES:
                    return fail("起点の熟語で試せる付け方がない")
                blanked = draw_new_start_blanks(start_word, start_tried)
                if blanked is None:
                    return fail("起点の熟語で試せる付け方がない")
                retries += 1
                start_tries += 1
                start_tried.add(blanked)
                state = State()
                register_word(state, start_word, blanked, False, START)
                break

            group = history[-1]

            # 段階1：子はそのままで、空欄の付け方を変える
            if group.blank_tries < MAX_BLANK_TRIES:
                assignment = draw_new_group_blanks(
                    group.children, group.parent, group.before.kanji_number, group.tried_patterns
                )
                if assignment is not None:
                    retries += 1
                    group.blank_tries += 1
                    group.pattern = pattern_key(assignment)
                    group.tried_patterns.add(group.pattern)
                    state = group.before.copy()
                    register_group(state, group, assignment)
                    break
                group.blank_tries = MAX_BLANK_TRIES   # 試せる付け方がないので段階2へ

            # 段階2：子を選び直す（子の数も抽選し直す）
            if group.child_tries < MAX_CHILD_TRIES:
                retries += 1
                group.child_tries += 1
                before = group.before
                children = pick_children(
                    group.candidates, choose_count(group, before, target_word_count),
                    no_shared_pair, group.parent, before.kanji_number
                )
                if not children:
                    continue   # 選べなかった：この回は失敗として数え、次を試す
                assignment = decide_group_blanks(children, group.parent, before.kanji_number)
                group.children = children
                group.pattern = pattern_key(assignment)
                group.tried_patterns = {group.pattern}
                group.blank_tries = 1
                state = before.copy()
                register_group(state, group, assignment)
                break

            # 段階3：1つ上の親（このグループの親の漢字を空欄にしたグループ）に戻る
            creator = group.creator
            while history and history[-1] is not creator:
                history.pop()
            if history:
                upper = history[-1]
                upper.blank_tries = 1
                upper.child_tries = 1
                upper.tried_patterns = {upper.pattern}
            # history が空なら、次の繰り返しで起点の熟語に戻る

    # ---- 仕上げ ----
    close_single_blanks(state.puzzle_words)
    if not is_consistent(state.puzzle_words):
        return fail("漢字と番号の対応が崩れている")

    stats = {
        "reached": True, "word_count": len(state.used_words), "skip_count": state.skip_count,
        "retries": retries, "start_word": start_word, "fail_reason": None,
    }
    return state.puzzle_words, stats
