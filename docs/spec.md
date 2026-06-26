# Maha Pothana

Maha Pothana is a SaaS Application for translating books. This can use for translating books with community support. The books can include more than 10000 pages and size will be more than 1Gb.

This has two main roles.

- Editor - Can add books for translating, organize the translated sections, pages.
- Translator - Can translate a part of the book.

## Main flows

### Authentication

- User need to use Google SSO for login to the system.
- The system automatically assign both editor and translator roles.
- Later, super admin can modify user's role and permission if need.
- User can upload books as a editor, then he can modify the book, he can assign other editors if need.
- User can see available translation needed items as a translate. Then he can translate them.
- Editor can invite to system users for translating his books. and block translators.

## Upload books

- User can upload books as a editor.
- User need to provide the book title and metadata manually for the uploading a book.
- The system should not allow to uploading same book again.
- After uploading a valid book then it should redirect to the book translate console.
- User should possible to see all uploaded documents with its thumbnail.
- User should possible to go the uploaded book console by clicking the list item.
- The book title and metadata should keep in the db with assigned book id.
- Uploaded documents should in a S3 bucket with book id.

## Separated to the pages

- After upload a book, it should automatically separated to the pages.
- Each pages should have page number for identification. It should start by 1 and increasing one by one until end of the book. Later editor can generate the actual page number.
- Separated pages should keep in a S3 bucket under the book id.

## Find sections of the page

- Editor should possible to process pages one by one.
- The system should show the detected sections of the page like Headers, paragraphs, footnotes, etc...
- The editor should possible to modify them.
- Show detected sections as editable rectangles overlaid on the image
- Let the editor drag/resize/delete/add rectangles
- The editor can confirm and export the separated sections
- Separated section should have a uniq id, and position detail for recreating the page again.

## Translate sections

- Translator should see the random separated section which need translate.
- The system should provide the automatic translated text, then translator just need to modify it if need.
- Translator should possible to see the entire page of the section, previous page of the section, next page of the section.
- Translator should possible to zoom the text.
- Translator should possible to add translator comment if need.
- The Editor can determine the no of translators for the book. Then same section will need to translate by n translators.

## Organize the book

- Editor can organize the book by adding/edit/delete pages.
- The editor should possible to add/edit/delete section of the page.
- The editor should possible to filter translation completed pages, sort by translated percentage.
- The editor should possible to see all available translations of the section if available.
- The editor can approve the correct translate. or he can give his own translation by giving translations.
- After finish the organize the book, editor can press button for build the finalized book.
- The finalized book should in the S3 bucket.
- The editor should possible to modify the finalized book again and again.

## Implementation

- Should starting from the offline setup
- All infrastructure should possible run locally.
- Only for Ai need to use free online models.
