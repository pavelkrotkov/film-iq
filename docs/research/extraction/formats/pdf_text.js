// Read-only first-page extraction using macOS PDFKit; no package installation.
ObjC.import('PDFKit');
function run(args) {
  const document = $.PDFDocument.alloc.initWithURL($.NSURL.fileURLWithPath(args[0]));
  return JSON.stringify({pages: Number(document.pageCount), text: ObjC.unwrap(document.pageAtIndex(0).string)});
}
