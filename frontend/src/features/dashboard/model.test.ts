import assert from "node:assert/strict";
import test from "node:test";

import { createDashboardModel } from "./model.js";

test("dashboard model exposes separated account strategy order and risk panels", () => {
  const model = createDashboardModel();

  assert.deepEqual(
    model.panels.map((panel) => panel.id),
    ["accounts", "strategies", "orders", "risk"],
  );
  assert.ok(model.panels.every((panel) => panel.source === "api-or-mock"));
});
