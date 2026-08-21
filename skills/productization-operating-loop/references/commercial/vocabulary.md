# Commercial-lane vocabulary

Scoped to the terms this lane's schema introduces. It does not restate the
twelve lanes or the ten rungs — those live in
[`../core/controlled-vocabulary.md`](../core/controlled-vocabulary.md) and
[`../core/evidence-ladder.md`](../core/evidence-ladder.md). This file is the
half a person reads before filling in
[`commercial-lane.schema.json`](commercial-lane.schema.json).

```text
BUYER_AND_PAYMENT_TRIGGER
  means         the economic decision-maker and the exact event that starts
                the payment obligation
  produced by   commercial-friction modelling against a named buyer
  consumed by   PRICE_HYPOTHESIS, the COMMERCIAL lane's PAID_VALIDATED rung
  never becomes a person who merely uses the thing. The user of a workflow and
                the payer for it are two separate claims; naming a buyer here
                is not evidence that this buyer exists.

COMMERCIAL_MODEL
  means         one of ONE_TIME, RECURRING, USAGE or SERVICE_ASSISTED — the
                shape of the payment obligation, not its price
  produced by   the same modelling pass as the buyer and trigger
  consumed by   PRICE_HYPOTHESIS, SALES_MOTION
  never becomes a claim that this shape fits this buyer. That fit is exactly
                what PAID_VALIDATED and REPEATABLE_COMMERCIAL exist to test.

PRICE_HYPOTHESIS
  means         a stated price, bound to a named buyer, with a falsifier
  produced by   pricing analysis
  consumed by   the COMMERCIAL lane, kill/iterate thresholds
  never becomes a price. A hypothesis with no buyer is not about anyone in
                particular, which is why the buyer is required on this field
                and not inherited from elsewhere in the record.

DELIVERY_COST_HYPOTHESIS
  means         what it is hypothesised to cost to deliver the priced unit
  produced by   the same pricing analysis, required alongside the price
  consumed by   margin reasoning, the kill/iterate threshold
  never becomes gross value on its own. A price with no delivery cost next to
                it describes revenue, not a business.

SALES_MOTION
  means         how the sale actually happens: self-serve, direct sales,
                partner-led, product-led, service-assisted, or free-trial-led
  produced by   observation or plan of the go-to-market path
  consumed by   the friction assessment, integration burden
  never becomes low friction by naming FREE_TRIAL_LED. A free trial that ends
                in an unstated cliff is a friction event deferred, not removed
                — which is why this motion carries its own required
                post-trial friction field.

INTEGRATION_BURDEN
  means         the new-account, API-key and integration cost the buyer clears
                before the priced unit does anything for them
  produced by   onboarding-flow analysis
  consumed by   TIME_TO_VALUE_BEFORE_PAYMENT, sales motion
  never becomes proof that a low stated burden is a low observed one. This
                field is a hypothesis, not an onboarding funnel measurement.

EXISTING_SUBSCRIPTION_LEVERAGE
  means         two independent booleans: whether a consumer subscription is
                present, and whether an API or integration entitlement is
                present
  produced by   entitlement research against the actual terms, not the brand
  consumed by   PRICE_HYPOTHESIS, SALES_MOTION
  never becomes one fact standing for both. A person's paid consumer
                subscription to a product is not, by default, an entitlement
                to call that product's API — the two are priced, sold and
                revoked independently, and this pair is closed specifically so
                no third field can assert the derivation.

TIME_TO_VALUE_BEFORE_PAYMENT
  means         how long before the buyer sees the priced unit do something
                useful, ahead of being asked to pay
  produced by   onboarding-flow analysis
  consumed by   SALES_MOTION, the kill/iterate threshold
  never becomes a claim about retention or repeat use past that first value
                moment.

IMPLEMENTATION_SUPPORT_BURDEN
  means         what it costs the seller, in labor, to get one buyer to first
                value and keep them there
  produced by   support-load analysis
  consumed by   DELIVERY_COST_HYPOTHESIS, SERVICE_ASSISTED classification
  never becomes zero by declaration. A stated zero-touch burden with no
                falsifier attached is exactly the overclaim this field's
                required falsifier is meant to block.

REFUND_CANCELLATION_REVERSAL_PATH
  means         what a buyer can actually do to stop or reverse the payment
                obligation, and how
  produced by   terms-of-service and billing-flow reading
  consumed by   the kill/iterate threshold, buyer trust reasoning
  never becomes evidence of low friction merely by existing. A refund path
                that requires an unlisted email round-trip is a different
                fact than a self-serve cancellation button.

EXPANSION_VALUE
  means         what an existing paying buyer is hypothesised to be worth
                beyond the first unit purchased
  produced by   usage-pattern and account-structure analysis
  consumed by   the kill/iterate threshold
  never becomes REPEATABLE_COMMERCIAL. Expansion inside one account is not a
                second distinct payer.

LEADING_METRIC / DECISIVE_METRIC
  means         a metric that moves before payment (leading) and a metric that
                is itself a transaction or repeated-transaction signal
                (decisive)
  produced by   instrumentation of the funnel and the ledger
  consumed by   the kill/iterate threshold
  never becomes interchangeable. An interest, usage or conversion signal
                cannot occupy the decisive slot — that is the schema's closed
                enum on that field, not a naming convention this note repeats
                for style.

KILL_ITERATE_THRESHOLD
  means         the stated numeric or observational cutoff at which this
                commercial hypothesis is abandoned or revised
  produced by   the program owner, stated before the read-back
  consumed by   the outcome disposition (PRESERVE / NARROW / ITERATE / KILL)
                in the parent program schema
  never becomes optional. A threshold set after the result is known is not a
                threshold.

REPEATABLE_COMMERCIAL_CLAIM
  means         an explicit claim, `claimed: true` or `false`, that this is a
                repeatable business rather than one payment
  produced by   counting distinct payers over time
  consumed by   the REPEATABLE_COMMERCIAL rung in the parent program's ladder
  never becomes true on one payment. `claimed: true` requires at least two
                distinct payment events in this record, which is the schema's
                own floor and still short of what the parent ladder's
                REPEATED_PAYMENT_SERIES receipt demands for the rung itself.
```
