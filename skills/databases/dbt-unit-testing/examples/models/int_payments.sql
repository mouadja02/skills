{{ config(materialized='ephemeral') }}
select payment_id, order_id, amount, status, paid_at
from {{ ref('stg_payments') }}
