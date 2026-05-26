import { afterEach, describe, expect, it, vi } from 'vitest'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'

import { ResearchDashboard } from '@/components/ResearchDashboard'
import { apiClient } from '@/api/client'

vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}))

describe('ResearchDashboard', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('loads research runs, reports, lifecycle status, decisions, and comparison output', async () => {
    const get = vi.mocked(apiClient.get)
    get.mockImplementation((url, config) => {
      if (url === '/backtests/research/runs') {
        return Promise.resolve([
          {
            run_id: 'exp-a',
            strategy_name: 'VWAP Pullback',
            strategy_version: '1',
            idea_id: 'idea-vwap',
            recorded_at: '2026-05-26T10:00:00+00:00',
            manifest_path: 'runs/research/exp-a.json',
            dataset_ids: ['gc-rth'],
            metrics: { total_return: 0.12, sharpe: 1.4 },
            artifact_hashes: {},
          },
          {
            run_id: 'exp-b',
            strategy_name: 'Mean Reversion',
            strategy_version: '1',
            idea_id: 'idea-mean',
            recorded_at: '2026-05-25T10:00:00+00:00',
            manifest_path: 'runs/research/exp-b.json',
            dataset_ids: ['spy-daily'],
            metrics: { total_return: 0.05, sharpe: 0.8 },
            artifact_hashes: {},
          },
        ])
      }
      if (url === '/backtests/research/reports') {
        return Promise.resolve([
          {
            evidence_bundle_id: 'bundle-a',
            workflow_run_id: 'workflow-a',
            strategy_id: 'vwap_pullback',
            idea_id: 'idea-vwap',
            report_path: 'reports/workflow.md',
            report_hash: 'report-hash',
            status: 'research_evidence_only',
            promotion_eligibility: 'not_reviewed',
            review_decisions: [{ decision: 'Needs More Evidence' }],
          },
        ])
      }
      if (url === '/backtests/research/reports/bundle-a') {
        return Promise.resolve({
          evidence_bundle_id: 'bundle-a',
          workflow_run_id: 'workflow-a',
          strategy_id: 'vwap_pullback',
          idea_id: 'idea-vwap',
          report_path: 'reports/workflow.md',
          report_hash: 'report-hash',
          status: 'research_evidence_only',
          promotion_eligibility: 'not_reviewed',
          review_decisions: [{ decision: 'Needs More Evidence' }],
          report_preview: '# Research Workflow Report\nAccepted evidence.',
        })
      }
      if (url === '/backtests/research/promotion-decisions') {
        return Promise.resolve([
          {
            decision_id: 'bundle-a:0',
            strategy_id: 'vwap_pullback',
            evidence_bundle_id: 'bundle-a',
            status: 'Needs More Evidence',
            source: 'evidence_review',
            decided_at: '2026-05-26T10:00:00+00:00',
            payload: {},
          },
        ])
      }
      if (url === '/backtests/research/lifecycle') {
        return Promise.resolve([
          {
            strategy_id: 'vwap_pullback',
            idea_id: 'idea-vwap',
            lifecycle_status: 'validated_research',
            promotion_status: 'review_required',
            latest_readiness_status: 'paper_candidate',
          },
        ])
      }
      if (url === '/backtests/research/compare') {
        expect(config).toEqual({
          params: {
            left_run_id: 'exp-a',
            right_run_id: 'exp-b',
            metric: 'total_return',
          },
        })
        return Promise.resolve({
          left_run_id: 'exp-a',
          right_run_id: 'exp-b',
          metric: 'total_return',
          left_value: 0.12,
          right_value: 0.05,
          delta: 0.06999999999999999,
        })
      }
      return Promise.resolve([])
    })

    render(<ResearchDashboard />)

    expect(await screen.findByText('Research Dashboard')).toBeInTheDocument()
    expect(await screen.findByText('VWAP Pullback')).toBeInTheDocument()
    expect(screen.getByText('validated_research')).toBeInTheDocument()
    expect(screen.getByText('Needs More Evidence')).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('Strategy filter'), { target: { value: 'VWAP' } })
    await waitFor(() => {
      expect(get).toHaveBeenCalledWith('/backtests/research/runs', {
        params: { strategy_name: 'VWAP' },
      })
    })

    fireEvent.change(screen.getByLabelText('Left run'), { target: { value: 'exp-a' } })
    fireEvent.change(screen.getByLabelText('Right run'), { target: { value: 'exp-b' } })
    fireEvent.click(screen.getByRole('button', { name: 'Compare runs' }))
    expect(await screen.findByText('Delta: 0.07')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Open report bundle-a' }))
    expect(await screen.findByText(/Accepted evidence/)).toBeInTheDocument()
  })
})
