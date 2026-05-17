import type { components } from '@/api/types.gen'

export type StrategyStatus = components['schemas']['StrategyStatusSchema']
export type StrategyStatusEntry = StrategyStatus
export type AccountSnapshot = components['schemas']['AccountSnapshotSchema']
export type OrderStatusEntry = components['schemas']['OrderStatusSchema']
export type BacktestRun = components['schemas']['BacktestRunSchema']
export type BacktestStrategyOption = components['schemas']['BacktestStrategyOptionSchema']
export type RuntimeCommandResponse = components['schemas']['RuntimeCommandResponseSchema']
export type RuntimeCommandResultResponse = components['schemas']['RuntimeCommandResultResponseSchema']
export type KillSwitchResponse = components['schemas']['KillSwitchResponseSchema']

export interface Position {
  instrument_id: string
  quantity: number
  average_price: number
  unrealized_pnl: number
  market_value: number
}

export interface RiskEvent {
  event_id: string
  rule_name: string
  reason: string
  event_time_utc: string
  severity: 'low' | 'medium' | 'high' | 'critical'
}
