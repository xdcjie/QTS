export type StrategyStatus = 'CREATED' | 'WARMING_UP' | 'ACTIVE' | 'PAUSED' | 'STOPPED' | 'FAILED'

export type OrderSide = 'BUY' | 'SELL'
export type OrderType = 'MARKET' | 'LIMIT' | 'STOP' | 'STOP_LIMIT'
export type OrderState = 'CREATED' | 'SENT' | 'PARTIALLY_FILLED' | 'FILLED' | 'CANCELED' | 'REJECTED'

export interface AccountSnapshot {
  account_id: string
  cash: Record<string, string>
}

export interface StrategyStatusEntry {
  strategy_id: string
  status: string
}

export interface OrderStatusEntry {
  order_id: string
  status: string
}

export interface BacktestRun {
  run_id: string
  config_path: string
  status: string
}

export interface BacktestStrategyOption {
  label: string
  config_path: string
}

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
