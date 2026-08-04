# Bushbash CTF Write-up - Beat Around The Bush

## Challenge Description
The challenge provides a long string of various nature-themed emojis and hints at the flag format: `bushbash{<words-separated-by-hyphens>}`.

**Ciphertext:**
`🌳🌲🌴🌵🎄🌿☘️🍀🍃🌴🍂🌵🍁🪴🌴🌵🌱🌴☘️🍂🌴🌾🌵🌳🌲🌴🌵🎋🎍🪴🌱🍂🌵🍁🪴🌴🌵🍂🎍☘️🍀🎍☘️🍀🪵🌵🌳🌲🌴🌵🍂🍃🌴🌴🪨🍃🌴🍂🍂🌵☘️🎍🍀🌲🌳🍂🌵🪴⛰️🍁🪴🌾 🍁☘️🌱🌵🌳🌲🌴🌵🍃⛰️🪴🎍🏕️🌴🌴🌳🍂🌵🍂🎍☘️🍀🪵🌵🎋🌿🍂🌲🎋🍁🍂🌲🌺🍂⛰️🌻🌼🍁☘️🌸🌻🌳🪴🌴🌴🍂🌻🍁☘️🌱🌻🏕️🍁☘️🍀🍁🪴⛰️⛰️🍂🪻🌵🎍☘️🌵🌳🌲🌴🌵🍃🍁☘️🌱 🌱⛰️🦌☘️🌵🌿☘️🌱🌴🪴🪵🌵🎄🌿🍂🌳🌵🌱⛰️☘️🦘🌳🌵🍀🌴🌳🌵🎋🎍🌳🌳🌴☘️🌵🎋🌸🌵🍁🌵🍂🪨🎍🌱🌴🪴🪵`

## Methodology

### 1. Initial Analysis
Looking at the ciphertext, we can observe a few key characteristics:
- The text consists entirely of emojis (mostly plants and a few animals/landscapes).
- The total number of unique emojis is 28. This is a very strong indicator of a **substitution cipher**, mapping to the 26 letters of the English alphabet plus a few punctuation marks (like spaces, commas, periods, or brackets).
- The flag format `bushbash{...}` suggests we should look for the emojis representing these specific letters to find the flag boundary.

### 2. Frequency Analysis & Common Patterns
In English, certain words and letters appear much more frequently than others. We can use this to our advantage.

- **The Separator:** The cactus emoji `🌵` appears 28 times, acting as a boundary between blocks of other emojis. This makes it highly likely to be the space character or a hyphen connecting words. Given the CTF context and the flag format hint, we assume `🌵 = -` (hyphen) and that the text is hyphen-separated.
- **The Word "the":** The sequence `🌳🌲🌴🌵` appears several times. In English, the most common three-letter word is "the". If `🌵` is a word boundary, then `🌳 = t`, `🌲 = h`, and `🌴 = e`.

### 3. Iterative Decryption (The "Wheel of Fortune" Method)
With our initial guesses (`t`, `h`, `e`, `-`), we can write a script to partially decrypt the text and leave unknown emojis as they are. This reveals fragments of words that we can logically deduce.

*Initial partial decryption:*
`the-🎄🌿☘️🍀🍃e🍂-🍁🪴e-🌱e☘️🍂e🌾-the-🎋🎍🪴🌱🍂-🍁🪴e-🍂🎍☘️🍀🎍☘️🍀🪵-the-🍂🍃ee🪨🍃e🍂🍂-☘️🎍🍀ht🍂-🪴⛰️🍁🪴🌾 🍁☘️🌱-the-🍃⛰️🪴🎍🏕️eet🍂-🍂🎍☘️🍀🪵-🎋🌿🍂h🎋🍁🍂h🌺🍂⛰️🌻🌼🍁☘️🌸🌻t🪴ee🍂🌻🍁☘️🌱🌻🏕️🍁☘️🍀🍁🪴⛰️⛰️🍂🪻-🎍☘️-the-🍃🍁☘️🌱 🌱⛰️🦌☘️-🌿☘️🌱e🪴🪵-🎄🌿🍂t-🌱⛰️☘️🦘t-🍀et-🎋🎍tte☘️-🎋🌸-🍁-🍂🪨🎍🌱e🪴🪵`

**Deduction Steps:**
1.  **`🍁🪴e` -> "are"**: A very common three-letter word ending in 'e' following "the [blank]". This gives us `🍁 = a` and `🪴 = r`.
2.  **`🍁☘️🌱` -> `a _ d` -> "and"**: The most logical fit for a three-letter word starting with 'a' and ending with 'd'. This gives `☘️ = n` and `🌱 = d`.
3.  **`🍃🍁☘️🌱 🌱⛰️🦌☘️-🌿☘️🌱e🪴🪵` -> `l a n d  d _ w n - u n d e r .`**: Given the kangaroo emoji and Australian theme of "bushbash", this phrase clearly spells "the land down under." This provides `🍃 = l`, `⛰️ = o`, `🦌 = w`, `🌿 = u`, and `🪵 = .` (period).
4.  **`🌱⛰️☘️🦘t` -> `d o n ' t`**: This reveals the kangaroo `🦘` acts as an apostrophe `'`.
5.  **Finding the Flag Wrapper**: We are looking for the word "bushbash". Using our known letters (`b u s h b a s h`), the sequence `🎋🌿🍂🌲🎋🍁🍂🌲` matches perfectly, confirming `🎋 = b` and `🍂 = s`.
6.  **Brackets and Internal Hyphens**: Following "bushbash", the `🌺` emoji must be `{` and `🪻` at the end of the sequence must be `}`. Inside the brackets, the sunflower `🌻` separates words, acting as the internal flag hyphen.

### 4. The Complete Emoji Dictionary
By completing the substitutions, we get the full mapping:

*   🍁 = a, 🎋 = b, 🌱 = d, 🌴 = e
*   🍀 = g, 🌲 = h, 🎍 = i, 🎄 = j
*   🏕️ = k, 🍃 = l, 🌼 = m, ☘️ = n
*   ⛰️ = o, 🪨 = p, 🪴 = r, 🍂 = s
*   🌳 = t, 🌿 = u, 🦌 = w, 🌸 = y
*   🌵 = - (word separator hyphen)
*   🌻 = - (flag hyphen)
*   🌺 = { , 🪻 = }
*   🌾 = , (comma) , 🪵 = . (period) , 🦘 = ' (apostrophe)

## The Solution

Running the full substitution cipher over the original ciphertext yields the complete plaintext message:

> `the-jungles-are-dense,-the-birds-are-singing.-the-sleepless-nights-roar, and-the-lorikeets-sing.-bushbash{so-many-trees-and-kangaroos}-in-the-land down-under.-just-don't-get-bitten-by-a-spider.`

Extracting the flag from within the curly braces gives us the final answer.

## Flag
`bushbash{so-many-trees-and-kangaroos}`
