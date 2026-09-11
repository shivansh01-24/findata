# Data Dictionary: UPI Fraud Intelligence Platform

**TransOrg AgentIQ Datathon Track 1 — FinTech & BFSI**  
*Document Version: 1.0.0 (Production Release)*

---

## 1. UPI Transactions (`trusted_transactions`)

| Field Name | Data Type | Source | Canonical Format | Description & Business Semantics | Quality / Transformation Rules |
|---|---|---|---|---|---|
| `txn_id` | String | Raw `txn_id` | `TXNxxxxxxxx` | Unique 8-digit zero-padded transaction reference. | Standardized from casing variations; exact duplicates removed with audit. |
| `timestamp` | String (ISO) | Raw `timestamp` | `YYYY-MM-DD HH:MM:SS` | Timestamp of transaction initiation. | Parsed from Unix epoch seconds, European `DD/MM/YYYY`, US `MM-DD-YYYY`, and 12h AM/PM. |
| `txn_date` | Date | Derived | `YYYY-MM-DD` | Calendar date for temporal grouping and trend aggregation. | Extracted from `timestamp`. |
| `hour_of_day` | Integer | Derived | `0 - 23` | Hour of day for velocity and diurnal analysis. | Extracted from `timestamp`. |
| `user_id` | String | Raw `user_id` | `USRxxxxx` | Payer customer identifier. | Standardized from `USR12345`, `usr12345`, `USR 12345`, `12345`. |
| `merchant_id` | String | Raw `merchant_id` | `MCHxxxx` | Payee merchant identifier. | Standardized from `MCH1234`, `mch1234`, `MCH-1234`, `1234`. |
| `merchant_category` | String | Master / MCC | Canonical Category | One of 10 standard merchant categories. | Resolved from transaction MCC or imputed from merchant master registry. |
| `effective_mcc` | String | Raw / Master | 4 digits (e.g. `5411`) | Standard ISO Merchant Category Code. | Normalized from floats (`5411.0`) and strings (`MCC-5411`). |
| `amount` | Float | Raw `amount` | Numeric (₹) | Transaction value in Indian Rupees. | Cleaned of `₹`, `Rs.`, `INR`, commas. Negative values preserved. |
| `amount_flag` | String | Derived | Enum | Classification of monetary amount. | `VALID_AMOUNT`, `REFUND_OR_REVERSAL_NEGATIVE`, `ZERO_AMOUNT`. |
| `status` | String | Raw `status` | `SUCCESS` \| `FAILED` \| `PENDING` | Final transaction lifecycle state. | Normalized from `S`, `Success`, `TXN_SUCCESS`, `COMPLETED`, `Fail`, `Declined`, etc. |
| `utr` | String | Raw `utr` | `UTRxxxxxxxxxx` | Unique Transaction Reference (10-digit). | Rescued from whitespace/hyphens (`UTR 2787678319` -> `UTR2787678319`). |
| `utr_flag` | String | Derived | Enum | UTR quality indicator. | `VALID_UTR`, `RESCUED_UTR_SPACES_REMOVED`, `MISSING_UTR`. |
| `customer_fk_valid` | Boolean | Derived | True / False | Foreign-key integrity against KYC master. | Validates whether payer account exists in customer registry. |
| `merchant_fk_valid` | Boolean | Derived | True / False | Foreign-key integrity against Merchant master. | Validates whether payee exists in merchant master registry. |

---

## 2. Customer KYC Master (`trusted_customers`)

| Field Name | Data Type | Source | Canonical Format | Description & Business Semantics | Quality / Transformation Rules |
|---|---|---|---|---|---|
| `user_id` | String | Raw `user_id` | `USRxxxxx` | Unique Golden Customer identifier. | Consolidated across duplicate KYC submissions. |
| `full_name` | String | Raw `full_name` | Title Cased | Customer legal name. | Cleaned of whitespace and casing anomalies. |
| `pan` | String | Raw `pan` | `[A-Z]{5}[0-9]{4}[A-Z]{1}` | Indian Permanent Account Number. | Whitespace removed; validated against Indian Tax PAN regex. |
| `pan_flag` | String | Derived | Enum | PAN validation status. | `VALID_PAN`, `MALFORMED_PAN_FORMAT`, `MISSING_PAN`. |
| `aadhaar` | String | Raw `aadhaar` | 12 digits or Masked | Government Unique Identity Number. | Stripped of spaces/hyphens; checks for shared credential syndicates. |
| `aadhaar_flag` | String | Derived | Enum | Aadhaar validation status. | `VALID_12_DIGIT_AADHAAR`, `MASKED_AADHAAR`, `MALFORMED_AADHAAR`. |
| `city` | String | Raw `city` | Title Cased | Residential City. | Standardized from abbreviations (`BLR` -> `Bangalore`, `LKO` -> `Lucknow`). |
| `state` | String | Raw `state` | Title Cased | State or Union Territory. | Standardized. |
| `monthly_income` | Float | Raw `monthly_income` | Numeric (₹) | Customer monthly income. | Rescued `k` suffix (`27.3k` -> `27300.0`), removed currency symbols. |
| `occupation` | String | Raw `occupation` | Title Cased | Employment category. | Standardized (`Salaried`, `Student`, `Self Employed`, etc.). |
| `signup_timestamp` | String | Raw | `YYYY-MM-DD HH:MM:SS` | Customer registration timestamp. | Standardized multi-format timestamp. |
| `kyc_status` | String | Raw `kyc_status` | `VERIFIED` \| `PENDING` \| `REJECTED` | Verified regulatory onboarding status. | Standardized from `Approved`, `Done`, `KYC_DONE`, `V`, `P`, `R`, etc. |
| `risk_segment` | String | Raw `risk_segment` | `LOW` \| `MEDIUM` \| `HIGH` \| `UNKNOWN` | Bank-assigned risk tier. | Standardized casing. |
| `resolution_type` | String | Derived | Enum | Method used to resolve raw records. | `SINGLETON`, `EXACT_DUPLICATE`, `FORMATTING_DUPLICATE`, `CONFLICTING_RECORD`. |
| `resolution_confidence` | Float | Derived | `0.0 - 1.0` | Confidence score in golden record. | 1.0 for singletons/exact dupes; 0.50 for records with conflicting PANs/names. |
| `conflict_details` | String | Derived | Free Text | Audit trail of conflicting raw attributes. | Documents specific conflicting fields (e.g. conflicting Aadhaar or KYC status). |

---

## 3. Merchants Master (`trusted_merchants`)

| Field Name | Data Type | Source | Canonical Format | Description & Business Semantics | Quality / Transformation Rules |
|---|---|---|---|---|---|
| `merchant_id` | String | Raw `merchant_id` | `MCHxxxx` | Unique Golden Merchant identifier. | Standardized to `MCH` + 4 digits. |
| `merchant_name` | String | Raw `merchant_name` | Title Cased | Commercial storefront name. | Resolved across conflicting entity submissions. |
| `mcc` | String | Raw `mcc` | 4 digits | Merchant Category Code. | Stripped of prefixes (`MCC-7011` -> `7011`). |
| `merchant_category` | String | Raw / MCC | Canonical Category | One of 10 standard categories. | Standardized from 82+ messy category strings. |
| `business_type` | String | Raw | Title Cased | Legal constitution. | `Private Limited`, `Partnership`, `Sole Proprietor`, `Individual`. |
| `city` / `state` | String | Raw | Title Cased | Business location. | Standardized. |
| `settlement_account` | String | Raw | Masked / Full Account | Bank account receiving payouts. | Audited for mule accounts shared across multiple distinct merchants. |
| `merchant_status` | String | Raw `merchant_status` | `ACTIVE` \| `INACTIVE` \| `SUSPENDED` | Gateway processing status. | Standardized from `Live`, `Enabled`, `Closed`, `Hold`, `Blocked`, etc. |
| `declared_avg_ticket_size`| Float | Raw | Numeric (₹) | Merchant stated average ticket size. | Cleaned of currencies and negative signs. |
| `avg_ticket` | Float | Derived | Numeric (₹) | Actual observed average ticket size. | Calculated from trusted UPI transactions. |
| `ticket_deviation_ratio` | Float | Derived | Numeric ratio | Ratio of actual to declared ticket size. | Identifies sudden behavioral spikes and transaction structuring. |
| `shared_settlement_account`| Boolean | Derived | True / False | Indicates account reuse across merchants. | Flag for mule syndicates and shell company networks. |
| `risk_score` | Float | Derived | `0.0 - 100.0` | Multivariate Merchant Risk Index. | Weighted composite score of chargebacks, ticket deviations, and mule flags. |
| `risk_level` | String | Derived | Enum | Risk categorization tier. | `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`. |

---

## 4. Chargebacks & Disputes (`trusted_chargebacks`)

| Field Name | Data Type | Source | Canonical Format | Description & Business Semantics | Quality / Transformation Rules |
|---|---|---|---|---|---|
| `complaint_id` | String | Raw `complaint_id` | `CBKxxxxxxx` | Unique dispute ticket identifier. | Deduplicated. |
| `txn_id` | String | Raw `txn_id` | `TXNxxxxxxxx` | Disputed transaction reference. | Standardized; linked against UPI transactions (91.52% match). |
| `user_id` | String | Raw `user_id` | `USRxxxxx` | Complainant customer identifier. | Standardized. |
| `merchant_id` | String | Raw `merchant_id` | `MCHxxxx` | Defendant merchant identifier. | Standardized. |
| `merchant_category` | String | Transaction / Master | Canonical Category | Merchant category under dispute. | Imputed from matched transaction or merchant master. |
| `transaction_timestamp` | String | Raw | `YYYY-MM-DD HH:MM:SS` | Timestamp of disputed transaction. | Standardized timestamp. |
| `reported_timestamp` | String | Raw | `YYYY-MM-DD HH:MM:SS` | Timestamp when customer logged dispute. | Standardized timestamp. |
| `reporting_delay_days` | Float | Derived | Days (Float) | Latency between transaction and dispute. | Identifies late detection and account takeover (ATO) patterns. |
| `disputed_amount` | Float | Raw / Imputed | Numeric (₹) | Disputed monetary amount. | Rescued empty amounts by imputing matched transaction amounts. |
| `amount_imputed` | Boolean | Derived | True / False | Indicates whether amount was imputed. | Audit flag for missing value rescue. |
| `reason_category` | String | Raw `reason_code` | Enum | Standardized dispute cause. | `Fraud & Account Takeover`, `Duplicate Debit & Billing`, `Service & Delivery Failure`, `Customer General Dispute`. |
| `severity` | String | Raw `severity` | `Critical` \| `High` \| `Medium` \| `Low` | Operational dispute priority. | Standardized from `CRIT`, `P1`, `H`, `M`, `L`, etc. |
| `resolution_status` | String | Raw `resolution_status`| `CLOSED` \| `RESOLVED` \| `IN_PROGRESS` \| `REJECTED` | Final dispute adjudication state. | Standardized from `WIP`, `Pending Bank`, etc. |
| `channel` | String | Raw `channel` | Title Cased | Intake channel. | `App`, `Branch`, `Call Center`, `Chatbot`, `Email`, `Ivr`. |
| `txn_link_valid` | Boolean | Derived | True / False | Validation of UPI transaction linkage. | Retains and flags 219 orphan disputes without false forcing. |

---

## 5. Standard Merchant Categories & MCC Alignment

| Canonical Category | Standard MCC | Sample Subcategories Mapped |
|---|---|---|
| **Transportation** | `4131` | Bus, Taxi, Travel, Transport, Logistics |
| **Telecom** | `4814` | Mobile Recharge, Phone Service, Telecommunications |
| **Department Store** | `5311` | Dept Store, Department Stores, Superstores |
| **Grocery** | `5411` | Kirana, Grocery Stores, Supermarkets, Provisions |
| **Apparel** | `5699` | Clothing, Fashion, Garments, Cloths |
| **Restaurant** | `5812` | Eating Places, Food Services, Cafes, Dining |
| **Pharmacy** | `5912` | Medical Store, Chemist, Pharmacies, Health |
| **Books & Stationery** | `5942` | Book Stores, Stationery, Periodicals |
| **Miscellaneous Retail**| `5999` | Specialty Retail, Misc Stores, Gift Shops |
| **Hotel & Lodging** | `7011` | Hotels, Motels, Lodging, Hospitality |
