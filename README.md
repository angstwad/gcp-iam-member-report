# Google Cloud Platform IAM Report Generator

## What is This?

This simple script generates a CSV report of IAM policy members throughout an organization or a subset thereof.  It assumes you prefer a CSV report to some other format and prefer manipulating the results with CSV tools, like Google Sheets or Excel.

## Requirements

* Python 3.6+
* [google-api-python-client](https://github.com/googleapis/google-api-python-client)


## Install

Getting up and running *could* be as simple as the below steps depending on your OS.  Take a look at each of the requirements' installation instructions for further guidance.

Git clone and install:
```
git clone https://github.com/angstwad/gcp-iam-member-report
cd gcp-iam-member-report
pip3 install .
```

Install from Git:
```
pip3 install git+https://github.com/angstwad/gcp-iam-member-report
```

Run:
```
gcp-iam-report --help
```

## Disclaimer

This is not an official Google product.
