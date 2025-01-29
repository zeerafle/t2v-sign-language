# t2v-sign-language documentation!

## Description

A way to translate text to video of sign language and vice versa using the latest generative AI capabilities

## Commands

The Makefile contains the central entry points for common tasks related to this project.

### Syncing data to cloud storage

* `make sync_data_up` will use `gsutil rsync` to recursively sync files in `data/` up to `gs://t2v-sign-language/data/`.
* `make sync_data_down` will use `gsutil rsync` to recursively sync files in `gs://t2v-sign-language/data/` to `data/`.


