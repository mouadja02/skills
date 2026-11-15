{{ config(materialized='table') }}
-- Synthetic inputs for a disposable local example only.
select
    cast(payment_id as integer) as payment_id,
    cast(order_id as integer) as order_id,
    cast(amount as decimal(12, 2)) as amount,
    cast(status as varchar) as status,
    cast(paid_at as timestamp) as paid_at
from (values
    (1, 10, 20.00, 'settled', '2026-01-01 00:00:00'),
    (2, 10, -5.00, 'settled', '2026-01-02 00:00:00'),
    (3, 20, 7.00, 'settled', '2026-01-01 00:00:00')
) as payments(payment_id, order_id, amount, status, paid_at)
