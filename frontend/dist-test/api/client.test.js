import assert from "node:assert/strict";
import test from "node:test";
import { ApiClient } from "./client.js";
test("API client calls backend health endpoint", async () => {
    const calls = [];
    const client = new ApiClient({
        baseUrl: "http://localhost:8000",
        fetcher: async (url) => {
            calls.push(String(url));
            return new Response(JSON.stringify({ status: "ok" }), { status: 200 });
        },
    });
    assert.deepEqual(await client.health(), { status: "ok" });
    assert.deepEqual(calls, ["http://localhost:8000/health"]);
});
