{{ config(materialized='incremental', unique_key='order_id') }}
-- Demo policy: full upstream payment history is available. Recompute complete
-- totals for changed orders; timestamp ties deliberately reprocess idempotently.
with payments as (
    select * from {{ ref('int_payments') }}
), changed_orders as (
    select distinct order_id
    from payments
    {% if is_incremental() %}
    where paid_at >= (
        select coalesce(max(last_payment_at), cast('1900-01-01' as timestamp))
        from {{ this }}
    )
    {% endif %}
)
select
    p.order_id,
    cast(sum(case when p.status = 'settled' then p.amount else 0 end) as decimal(12, 2)) as revenue,
    max(p.paid_at) as last_payment_at
from payments p
inner join changed_orders c on c.order_id = p.order_id
group by p.order_id
