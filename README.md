# Sogou User Dict Converter

A tool to extract and decrypt the user dictionary file from Sogou IME. It rescues your data from
Sogou's evil hands.

## Requirements

* Python3

## Usage

```sh
python3 parse.py <input-bin-dict> <output-tsv>
```

* `input-bin-dict`: The binary dictionary file exported from Sogou IME (usually "搜狗词库备份_x.bin").
* `output-tsv`: The output TSV file with the words and the frequencies.
