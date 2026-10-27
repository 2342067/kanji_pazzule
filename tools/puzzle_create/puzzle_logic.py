import random
from collections import defaultdict, deque

# ==== パラメータ ====
ADDITIONAL_BLANK_PROBABILITY = 0.4   # 残り文字1つごとに独立適用
FORCE_BRANCH_HINT_INTERVAL = 2       # 経路上でヒントなしがこの回数連続しないよう、次の展開を強制的に2分岐にする


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


def decide_group_blanks(picked_words, frontier_kanji):
    """
    1回のfrontier展開で選ばれた熟語グループ（1〜2個）について、
    各熟語の追加空欄（frontier_kanji以外の空欄）を決める。

    グループ単位で以下の2つを保証する:
      - 新規空欄の最低保証: グループ内のどれか1つは必ず新規空欄を持つ（連鎖を止めない）
      - ヒントの最低保証: 可能なら、グループ内のどれか1つは既知文字を残す
        （両立できない場合は新規空欄の保証を優先し、ヒント保証は諦める）

    戻り値: {word: (remaining_chars, blanked_chars)}
    """
    assignments = {}
    for word in picked_words:
        remaining = sorted(set(word) - {frontier_kanji})
        blanked = {c for c in remaining if random.random() < ADDITIONAL_BLANK_PROBABILITY}
        assignments[word] = [remaining, blanked]

    # ---- 新規空欄の最低保証 ----
    if all(len(blanked) == 0 for _, blanked in assignments.values()):
        word = random.choice(picked_words)
        remaining, blanked = assignments[word]
        blanked.add(random.choice(remaining))

    # ---- ヒントの最低保証（可能なら） ----
    if all(len(remaining) == len(blanked) for remaining, blanked in assignments.values()):
        for word in picked_words:
            remaining, blanked = assignments[word]
            if len(blanked) == 0:
                continue
            other_words_have_blank = any(
                len(assignments[w][1]) > 0 for w in picked_words if w != word
            )
            # このword自身から1文字外しても、グループ全体で見て新規空欄が0にならなければ外してよい
            if len(blanked) > 1 or other_words_have_blank:
                keep_char = random.choice(sorted(blanked))
                blanked.discard(keep_char)
                break
        # どの熟語からも外せない（グループが1個の2字熟語のみ）場合は、空欄保証を優先して諦める

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
    frontier = deque()      # 未展開の空欄漢字。要素は (漢字, その経路の連続ヒントなし数)
    next_number = 1
    skip_count = 0

    def register_word(word, blanked_chars, extra_blank_count_for_streak):
        """
        熟語をused_wordsとpuzzle_wordsに登録し、新規空欄をfrontierに積む。
        extra_blank_count_for_streak: この熟語がヒントを残せたか（0）、残せなかったか（親のstreak+1）
        """
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
            frontier.append((ch, extra_blank_count_for_streak))
        puzzle_words.append({"word": word, "blanks": blanks})

    # ---- 起点となる熟語を選ぶ（グループ保証の対象外。必ず1文字以上空欄にする） ----
    start_word = random.choice(words)
    start_chars = sorted(set(start_word))
    blanked = {c for c in start_chars if random.random() < ADDITIONAL_BLANK_PROBABILITY}
    if not blanked:
        blanked = {random.choice(start_chars)}
    hint_preserved = len(blanked) < len(start_chars)
    register_word(start_word, blanked, 0 if hint_preserved else 1)

    # ---- キューを使って展開 ----
    while len(used_words) < target_word_count and frontier:
        frontier_kanji, streak = frontier.popleft()
        candidates = get_candidates(frontier_kanji, kanji_to_words, used_words, kanji_number)

        if not candidates:
            skip_count += 1
            continue

        force_branch = streak >= FORCE_BRANCH_HINT_INTERVAL - 1
        if force_branch and len(candidates) >= 2:
            n_pick = 2
        else:
            n_pick = min(random.choice([1, 2]), len(candidates))
        picked = random.sample(candidates, n_pick)

        assignments = decide_group_blanks(picked, frontier_kanji)

        for word in picked:
            if len(used_words) >= target_word_count:
                break
            if word in used_words:
                continue
            remaining, blanked = assignments[word]
            hint_preserved = len(blanked) < len(remaining)
            next_streak = 0 if hint_preserved else streak + 1
            register_word(word, blanked | {frontier_kanji}, next_streak)

    stats = {
        "reached": len(used_words) >= target_word_count,
        "word_count": len(used_words),
        "skip_count": skip_count,
        "start_word": start_word,
    }
    return puzzle_words, stats