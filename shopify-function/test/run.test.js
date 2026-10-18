import assert from "node:assert/strict";
import test from "node:test";

import {cartLinesDiscountsGenerateRun} from "../src/run.js";

function input({quantity = 12, eligible = "true", config = null} = {}) {
  return {
    cart: {
      lines: [
        {
          id: "gid://shopify/CartLine/1",
          quantity,
          merchandise: {
            __typename: "ProductVariant",
            product: {metafield: {value: eligible}},
          },
        },
      ],
    },
    discount: {metafield: {jsonValue: config}},
  };
}

test("discounts an eligible 12-bottle case with safe defaults", () => {
  const result = cartLinesDiscountsGenerateRun(input());
  const candidate = result.operations[0].productDiscountsAdd.candidates[0];
  assert.equal(candidate.value.percentage.value, 10);
  assert.equal(candidate.targets[0].cartLine.id, "gid://shopify/CartLine/1");
});

test("does not discount an ineligible product", () => {
  assert.deepEqual(cartLinesDiscountsGenerateRun(input({eligible: "false"})), {operations: []});
});

test("does not discount fewer than the configured case size", () => {
  const config = {minimumQuantity: 6, percentage: 15};
  assert.deepEqual(cartLinesDiscountsGenerateRun(input({quantity: 5, config})), {operations: []});
});

test("uses merchant configuration from an app-owned metafield", () => {
  const result = cartLinesDiscountsGenerateRun(
    input({quantity: 6, config: {minimumQuantity: 6, percentage: 15}}),
  );
  assert.equal(result.operations[0].productDiscountsAdd.candidates[0].value.percentage.value, 15);
});

