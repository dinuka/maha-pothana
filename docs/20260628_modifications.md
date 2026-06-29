# Modification after 1st implementation

## @data-model.md

- The book should have property for setting translate need languages.
- The page should have another page number which need to use for translated book. It may differ from the sequential number. May be come from the original page. It will include roman numbers or arabic numbers with or without parenthesis. As example, i, (II), 1, 1b, etc...
- Section should have the cropped image.
- Translation should have optional field for keeping another translation to exact letters. As example devanagari word should have exact Sinhala letter word. As example
  - Original text - माता
  - Sinhala script - මාතා
  - Sinhala translator - අම්මා

## @user-stories.md

- US-4.5 Configurable Translator Count - Translator never sees their own previous translation.
  - Translator should possible to see his own translation before the editor approve or reject, but not others. But after approving one translator should possible to see other translation then he can argive or ask questions as a comment. Editor can see such comments and reply or change the approved translation.

- US-5.3 Review Translations
  - The editor should possible to approve N translations if N translation give same translation or editor translate his own translation using provided translation. Also editor can reject the N translation if not correct. The translators are need to translate section until has at least one translation.

## @architecture.md

- Need to use Mongo db instead of Postgress sql
- S3 should include images of sections as well.
