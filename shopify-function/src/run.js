// Pure logic shaped for Shopify's cart.lines.discounts.generate.run target.
// A Shopify CLI scaffold supplies generated types and compiles this module to Wasm.

export function cartLinesDiscountsGenerateRun(input) {
  const config = input.discount?.metafield?.jsonValue ?? {};
  const minimumQuantity = positiveNumber(config.minimumQuantity, 12);
  const percentage = boundedPercentage(config.percentage, 10);

  const candidates = input.cart.lines
    .filter(isEligibleWineLine)
    .filter((line) => line.quantity >= minimumQuantity)
    .map((line) => ({
      message: `${percentage}% case discount`,
      targets: [{cartLine: {id: line.id}}],
      value: {percentage: {value: percentage}},
    }));

  if (candidates.length === 0) return {operations: []};

  return {
    operations: [
      {
        productDiscountsAdd: {
          candidates,
          selectionStrategy: "ALL",
        },
      },
    ],
  };
}

function isEligibleWineLine(line) {
  return (
    line.merchandise?.__typename === "ProductVariant" &&
    line.merchandise.product?.metafield?.value === "true"
  );
}

function positiveNumber(value, fallback) {
  return Number.isFinite(value) && value > 0 ? value : fallback;
}

function boundedPercentage(value, fallback) {
  return Number.isFinite(value) && value > 0 && value <= 100 ? value : fallback;
}

