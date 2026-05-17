import { expect, test } from '@playwright/test'

const API_MOCKS: Record<string, string> = {
  '/api/strategies': JSON.stringify([]),
  '/api/backtests': JSON.stringify([]),
  '/api/backtests/strategy-options': JSON.stringify([]),
  '/api/accounts': JSON.stringify([]),
  '/api/orders': JSON.stringify([]),
  '/api/operations/runtime/state': JSON.stringify({ state: 'running' }),
  '/api/operations/kill-switches': JSON.stringify({
    scope: 'global',
    scope_id: null,
    active: false,
    reason: '',
  }),
}

test.beforeEach(async ({ page }) => {
  await page.route('**/api/**', (route) => {
    const url = new URL(route.request().url())
    if (!url.pathname.startsWith('/api/')) {
      return route.continue()
    }

    const response = API_MOCKS[url.pathname]
    if (response !== undefined) {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: response,
      })
      return
    }
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({}),
    })
  })
  await page.goto('/')
})

test('Dashboard smoke route renders', async ({ page }) => {
  await expect(page.getByRole('heading', { name: 'Overview' })).toBeVisible()
})

test('Strategies smoke route renders', async ({ page }) => {
  await page.getByRole('button', { name: 'Strategies' }).click()
  await expect(page.getByRole('heading', { name: 'Strategies' })).toBeVisible()
})

test('BacktestLab smoke route renders', async ({ page }) => {
  await page.getByRole('button', { name: 'Backtest Lab' }).click()
  await expect(page.getByRole('heading', { name: 'Backtest Lab' })).toBeVisible()
})

test('Operations smoke route renders', async ({ page }) => {
  await page.getByRole('button', { name: 'Operations' }).click()
  await expect(page.getByRole('heading', { name: 'Operations' })).toBeVisible()
})
