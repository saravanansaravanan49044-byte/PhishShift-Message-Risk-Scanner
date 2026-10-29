# EDA summary

Raw rows: 432  |  after cleaning+dedup: 93

## Empty-string counts per column (raw)
message_id                  0
channel                     0
subject_or_title          217
body_text                   0
sanitized_url_features      0
sender_domain_type          1
label                       0
campaign_group              0
collected_date              0
source                      0
license                     0

## Label balance (clean)
label
1    67
0    26

## Channel x label
label     0   1
channel        
email    16  32
sms      10  35

## Sender domain type x label (LEAKAGE RISK: near-perfectly separates classes)
label                0   1
sender_domain_type        
free_mail            0  24
internal            26   0
lookalike            0  25
unknown              0   1
unknown_external     0  17

## Body length stats
count     93.0
mean     105.2
std       21.7
min       64.0
25%       86.0
50%      105.0
75%      121.0
max      144.0

Leakage notes: sender_domain_type and url features are strongly label-correlated in synthetic data; campaign_group must never be a feature; dates are uniformly random so time ordering is not informative.