import math
import random
from collections import defaultdict, deque

# ==== パラメータ ====
ADDITIONAL_BLANK_PROBABILITY = 0.4                # 残り文字1つごとに独立適用
CHILD_COUNT_WEIGHTS = {2: 0.5, 3: 0.3, 4: 0.2}    # 1つの親から選ぶ子の数とその確率
FORCED_CHILD_COUNT = 4                            # 子が1個しか選べなかった場合、その子が作った空欄から選ぶ子の数


def build_graph(words):
    """漢字 -> 熟語リスト、の対応表を構築する"""
    kanji_to_words = defaultdict(list)
    for word in words:
        for k in set(word):  # 同じ漢字が複数回出る熟語でも重複登録しない
            kanji_to_words[k].append(word)
    return kanji_to_words


def get_candidates(frontier_kanji, kanji_to_words, used_words, kanji_number):
    """frontier_kanjiを含み、他の既確定漢字を含まない未使用熟語を候補として返す"""
    candidates = []
    for word in kanji_to_words.get(frontier_kanji, []):
        if word in used_words:
            continue
        conflict = any(k != frontier_kanji and k in kanji_number for k in word)
        if conflict:
            continue
        candidates.append(word)
    return candidates


def decide_child_count():
    """1つの親から選ぶ子の数を、CHILD_COUNT_WEIGHTS の確率で決める"""
    counts = list(CHILD_COUNT_WEIGHTS.keys())
    weights = list(CHILD_COUNT_WEIGHTS.values())
    return random.choices(counts, weights=weights)[0]


def decide_group_blanks(picked_words, frontier_kanji):
    """
    1つの親から選ばれた子の熟語グループについて、
    各熟語の追加空欄（frontier_kanji以外の空欄）を決める。

    グループ単位で以下の2つを保証する:
      - 新規空欄の最低保証: グループ内のどれか1つは必ず新規空欄を持つ（連鎖を止めない）
      - ヒントの保証: 子が2個以上のとき、半分以上（切り上げ）の熟語は見える漢字を1つ以上残す
        子が1個のときは新規空欄の保証を優先する

    戻り値: {word: (remaining_chars, blanked_chars)}
    """
    assignments = {}
    for word in picked_words:
        remaining = sorted(set(word) - {frontier_kanji})
        blanked = {c for c in remaining if random.random() < ADDITIONAL_BLANK_PROBABILITY}
        assignments[word] = [remaining, blanked]

    def total_new_blanks():
        return sum(len(b) for _, b in assignments.values())

    def has_hint(word):
        remaining, blanked = assignments[word]
        return len(blanked) < len(remaining)

    # ---- 新規空欄の最低保証 ----
    if total_new_blanks() == 0:
        words_with_remaining = [w for w in picked_words if assignments[w][0]]
        if words_with_remaining:
            word = random.choice(words_with_remaining)
            remaining, blanked = assignments[word]
            blanked.add(random.choice(remaining))

    # ---- ヒントの保証（子が2個以上のとき、半分以上） ----
    if len(picked_words) >= 2:
        required = math.ceil(len(picked_words) / 2)
        no_hint = [w for w in picked_words if not has_hint(w)]
        random.shuffle(no_hint)
        for word in no_hint:
            if sum(1 for w in picked_words if has_hint(w)) >= required:
                break
            remaining, blanked = assignments[word]
            if not blanked:
                continue  # 残す文字がない熟語（同じ漢字の繰り返しなど）は対象外
            # 1文字外しても、グループ全体で新規空欄が0にならなければ外す
            if total_new_blanks() > 1:
                blanked.discard(random.choice(sorted(blanked)))

    return {word: (r, b) for word, (r, b) in assignments.items()}


def generate_puzzle(words, target_word_count, seed=None):
    """
    1つのパズルを生成する。
    戻り値:
        puzzle_words: [{"word": str, "blanks": {index: (kanji, number)}}, ...]
        stats: {"reached": bool, "word_count": int, "skip_count": int, "start_word": str}
    """
    if seed is not None:
        random.seed(seed)

    kanji_to_words = build_graph(words)

    used_words = []
    kanji_number = {}       # 漢字 -> 番号
    puzzle_words = []       # 生成された熟語と空欄情報
    frontier = deque()      # 未展開の空欄漢字。要素は (漢字, 子を4個選ぶかどうか)
    next_number = 1
    skip_count = 0

    def register_word(word, blanked_chars, force_next):
        """熟語をused_wordsとpuzzle_wordsに登録し、新規空欄をfrontierに積む"""
        nonlocal next_number
        used_words.append(word)
        blanks = {}
        new_kanji = []
        for i, ch in enumerate(word):
            if ch in blanked_chars and ch not in kanji_number:
                kanji_number[ch] = next_number
                next_number += 1
                new_kanji.append(ch)
            if ch in kanji_number:
                blanks[i] = (ch, kanji_number[ch])
        for ch in new_kanji:
            frontier.append((ch, force_next))
        puzzle_words.append({"word": word, "blanks": blanks})

    # ---- 起点となる熟語を選ぶ（必ず1文字以上空欄にする） ----
    start_word = random.choice(words)
    start_chars = sorted(set(start_word))
    blanked = {c for c in start_chars if random.random() < ADDITIONAL_BLANK_PROBABILITY}
    if not blanked:
        blanked = {random.choice(start_chars)}
    register_word(start_word, blanked, False)

    # ---- キューを使って展開 ----
    while len(used_words) < target_word_count and frontier:
        frontier_kanji, force_four = frontier.popleft()
        candidates = get_candidates(frontier_kanji, kanji_to_words, used_words, kanji_number)

        if not candidates:
            skip_count += 1
            continue

        wanted = FORCED_CHILD_COUNT if force_four else decide_child_count()
        n_pick = min(wanted, len(candidates))
        picked = random.sample(candidates, n_pick)
        # 子が1個しか選べなかった場合、その子が作った空欄からは4個選ぶ
        force_next = n_pick == 1

        assignments = decide_group_blanks(picked, frontier_kanji)

        for word in picked:
            if len(used_words) >= target_word_count:
                break
            if word in used_words:
                continue
            remaining, blanked = assignments[word]
            register_word(word, blanked | {frontier_kanji}, force_next)

    stats = {
        "reached": len(used_words) >= target_word_count,
        "word_count": len(used_words),
        "skip_count": skip_count,
        "start_word": start_word,
    }
    return puzzle_words, stats