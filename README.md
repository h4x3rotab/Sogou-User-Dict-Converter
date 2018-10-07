# Sogou-User-Dict-Converter

A tool to extract and decrypt the user dictionary (so called "usrDictV3") file from Sogou IME.
Sogou shouldn't hold your data while disallowing you to access the data. This tool rescues your data
from Sogou's evil hands.

## License

This software is released under the terms of [GPLv3 license](https://www.gnu.org/licenses/gpl-3.0.html).

## Requirements

* Python3

## Usage

```sh
python3 parse.py <input-bin-dict> <output-tsv>
```

* `input-bin-dict`: The binary dictionary file exported from Sogou IME (usually "搜狗词库备份_x.bin").
* `output-tsv`: The output TSV file with the words and the frequencies.
