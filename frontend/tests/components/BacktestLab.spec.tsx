import { afterEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

import { BacktestLab } from '@/components/BacktestLab'
import { apiClient } from '@/api/client'

vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

describe('BacktestLab', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders backtest lab and loads strategy options', async () => {
    const get = vi.mocked(apiClient.get)
    get.mockImplementation((url) => {
      if (url === '/backtests') return Promise.resolve([])
      if (url === '/backtests/strategy-options') return Promise.resolve([{ config_path: 'examples/ema.yaml', label: 'EMA Cross' }])
      return Promise.resolve([])
    })

    render(<BacktestLab />)

    expect(screen.getByText('Backtest Lab')).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getByText('No backtest runs yet. Configure and click Run Simulation.')).toBeInTheDocument()
    })
  })

  it('adds a new run when simulation endpoint succeeds', async () => {
    const get = vi.mocked(apiClient.get)
    const post = vi.mocked(apiClient.post)
    get.mockImplementation((url) => {
      if (url === '/backtests') return Promise.resolve([])
      if (url === '/backtests/strategy-options') {
        return Promise.resolve([{ config_path: 'examples/ema.yaml', label: 'EMA Cross' }])
      }
      return Promise.resolve([])
    })
    post.mockResolvedValue({
      run_id: 'run-001',
      status: 'completed',
      config_path: 'examples/ema.yaml',
    } as never)

    render(<BacktestLab />)
    await screen.findByText('EMA Cross')
    const runButton = await screen.findByRole('button', { name: 'Run Simulation' })
    await waitFor(() => expect(runButton).not.toBeDisabled())
    fireEvent.click(runButton)

    await waitFor(() => {
      expect(post).toHaveBeenCalledWith('/backtests', { config_path: 'examples/ema.yaml' })
    })
    await waitFor(() => {
      expect(
        screen.getByText((value) => value.replace(/\s+/g, ' ').includes('run-001'))
      ).toBeInTheDocument()
    })
  })
})
