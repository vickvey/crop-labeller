// Config for regenerating USAGE-GUIDELINES.pdf (see README, "Development"):
//   npx md-to-pdf --config-file scripts/pdf/md-to-pdf.config.cjs USAGE-GUIDELINES.md
const path = require("path");

module.exports = {
  stylesheet: [path.join(__dirname, "usage-guidelines.css")],
  pdf_options: {
    format: "A4",
    margin: { top: "18mm", bottom: "20mm", left: "18mm", right: "18mm" },
    printBackground: true,
    displayHeaderFooter: true,
    headerTemplate: "<div></div>",
    footerTemplate:
      '<div style="width:100%; font-size:8pt; color:#6e7781; padding:0 18mm; display:flex; justify-content:space-between;">' +
      "<span>Crop Labeller — Researcher Guide</span>" +
      '<span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>',
  },
};
