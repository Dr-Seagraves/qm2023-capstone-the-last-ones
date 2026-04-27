const fs = require("fs");
const {
  Document,
  Packer,
  Paragraph,
  TextRun,
  HeadingLevel,
  AlignmentType,
  LevelFormat,
  PageBreak,
} = require("docx");

const bulletsRef = "bullets";

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 24 } } },
    paragraphStyles: [
      {
        id: "Heading1",
        name: "Heading 1",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 32, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 240, after: 240 }, outlineLevel: 0 },
      },
      {
        id: "Heading2",
        name: "Heading 2",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 28, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 180, after: 180 }, outlineLevel: 1 },
      },
    ],
  },
  numbering: {
    config: [
      {
        reference: bulletsRef,
        levels: [
          {
            level: 0,
            format: LevelFormat.BULLET,
            text: "•",
            alignment: AlignmentType.LEFT,
            style: { paragraph: { indent: { left: 720, hanging: 360 } } },
          },
        ],
      },
    ],
  },
  sections: [
    {
      properties: {
        page: {
          size: { width: 12240, height: 15840 },
          margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
        },
      },
      children: [
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: "Investment Memo", bold: true, size: 36 }),
          ],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun("Energy Price Shocks and Inflation Pass-Through"),
          ],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun("April 27, 2026")],
        }),
        new Paragraph({ children: [new PageBreak()] }),

        new Paragraph({
          heading: HeadingLevel.HEADING_1,
          children: [new TextRun("Executive Summary")],
        }),
        new Paragraph({
          numbering: { reference: bulletsRef, level: 0 },
          children: [
            new TextRun(
              "Estimated pass-through from gas import shocks to inflation is small and statistically insignificant in the baseline fixed-effects model."
            ),
          ],
        }),
        new Paragraph({
          numbering: { reference: bulletsRef, level: 0 },
          children: [
            new TextRun(
              "No robust evidence shows stronger pass-through in high-energy-dependence countries relative to low-dependence countries."
            ),
          ],
        }),
        new Paragraph({
          numbering: { reference: bulletsRef, level: 0 },
          children: [
            new TextRun(
              "Robustness checks across lags, subsamples, and a placebo DiD confirm the weak and imprecise effects."
            ),
          ],
        }),
        new Paragraph({
          numbering: { reference: bulletsRef, level: 0 },
          children: [
            new TextRun(
              "Key limitations include using gas-import growth as a proxy for price shocks and annual inflation aggregation that can mute short-run effects."
            ),
          ],
        }),

        new Paragraph({
          heading: HeadingLevel.HEADING_1,
          children: [new TextRun("Research Question and Hypotheses")],
        }),
        new Paragraph({
          children: [
            new TextRun(
              "Research question: How strongly do oil and gas price shocks pass through to consumer inflation, and does pass-through differ between high- and low-energy-dependence countries?"
            ),
          ],
        }),
        new Paragraph({
          children: [
            new TextRun(
              "Core hypotheses: (1) positive shocks increase inflation, (2) pass-through is stronger in high-dependence countries, (3) pass-through may be asymmetric for positive versus negative shocks."
            ),
          ],
        }),

        new Paragraph({
          heading: HeadingLevel.HEADING_1,
          children: [new TextRun("Data and Method")],
        }),
        new Paragraph({
          numbering: { reference: bulletsRef, level: 0 },
          children: [
            new TextRun(
              "Panel combining JODI energy flows and WDI macro indicators with country and year fixed effects."
            ),
          ],
        }),
        new Paragraph({
          numbering: { reference: bulletsRef, level: 0 },
          children: [
            new TextRun(
              "Shock proxy: lagged gas-import growth; interaction with a high-energy-dependence indicator."
            ),
          ],
        }),
        new Paragraph({
          numbering: { reference: bulletsRef, level: 0 },
          children: [
            new TextRun(
              "Model A: two-way fixed effects; Model B: DiD with post-2022 treatment for high-dependence countries."
            ),
          ],
        }),

        new Paragraph({
          heading: HeadingLevel.HEADING_1,
          children: [new TextRun("Key Findings")],
        }),
        new Paragraph({
          children: [
            new TextRun(
              "Baseline coefficients (annual inflation percentage points):"
            ),
          ],
        }),
        new Paragraph({
          numbering: { reference: bulletsRef, level: 0 },
          children: [
            new TextRun(
              "Lagged gas-import shock: -0.0001 (p = 0.887)."
            ),
          ],
        }),
        new Paragraph({
          numbering: { reference: bulletsRef, level: 0 },
          children: [
            new TextRun(
              "Shock x high-dependence interaction: -0.0005 (p = 0.596)."
            ),
          ],
        }),
        new Paragraph({
          numbering: { reference: bulletsRef, level: 0 },
          children: [
            new TextRun(
              "DiD interaction (post-2022 x high dependence): -0.2502 (p = 0.811)."
            ),
          ],
        }),
        new Paragraph({
          children: [
            new TextRun(
              "Robustness checks across alternative lags, exclusion of 2020, and subsamples yielded similarly small, insignificant effects."
            ),
          ],
        }),

        new Paragraph({
          heading: HeadingLevel.HEADING_1,
          children: [new TextRun("Interpretation vs Hypotheses")],
        }),
        new Paragraph({
          numbering: { reference: bulletsRef, level: 0 },
          children: [
            new TextRun(
              "Hypothesis 1 (positive pass-through): not supported by statistically significant evidence; estimated effect is near zero."
            ),
          ],
        }),
        new Paragraph({
          numbering: { reference: bulletsRef, level: 0 },
          children: [
            new TextRun(
              "Hypothesis 2 (stronger in high dependence): not supported; interaction is negative and insignificant."
            ),
          ],
        }),
        new Paragraph({
          numbering: { reference: bulletsRef, level: 0 },
          children: [
            new TextRun(
              "Hypothesis 3 (asymmetry): not tested in this baseline and remains an open extension."
            ),
          ],
        }),

        new Paragraph({
          heading: HeadingLevel.HEADING_1,
          children: [new TextRun("Risks and Limitations")],
        }),
        new Paragraph({
          numbering: { reference: bulletsRef, level: 0 },
          children: [
            new TextRun(
              "Shock proxy is based on import growth rather than a direct global oil or gas price series."
            ),
          ],
        }),
        new Paragraph({
          numbering: { reference: bulletsRef, level: 0 },
          children: [
            new TextRun(
              "Annual inflation and aggregated energy flows can attenuate short-run pass-through."
            ),
          ],
        }),
        new Paragraph({
          numbering: { reference: bulletsRef, level: 0 },
          children: [
            new TextRun(
              "Remaining omitted-variable risks include monetary policy, exchange rates, and stabilization responses."
            ),
          ],
        }),

        new Paragraph({
          heading: HeadingLevel.HEADING_1,
          children: [new TextRun("Recommendations and Next Steps")],
        }),
        new Paragraph({
          numbering: { reference: bulletsRef, level: 0 },
          children: [
            new TextRun(
              "Test with a direct price series (e.g., Brent or global gas index) for a sharper shock measure."
            ),
          ],
        }),
        new Paragraph({
          numbering: { reference: bulletsRef, level: 0 },
          children: [
            new TextRun(
              "Use higher-frequency inflation where available to capture short-run dynamics."
            ),
          ],
        }),
        new Paragraph({
          numbering: { reference: bulletsRef, level: 0 },
          children: [
            new TextRun(
              "Estimate asymmetric effects by separating positive and negative shocks."
            ),
          ],
        }),
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync("/workspaces/qm2023-capstone-the-last-ones/investment_memo.docx", buffer);
});
