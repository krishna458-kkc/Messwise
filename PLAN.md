

## PREDICT
## PLAN
## COOKMEASURE
## LEARN
closed loop
## HACKATHON PROJECT DOCUMENTATION
MessWise
AI food-operations intelligence for
hostel messes, canteens and institutional kitchens
## Predict.  Plan.  Cook.  Measure.  Learn.  Save.
Prevent surplus before it is cooked  ·  prove the savings with real kitchen data
## Integrated Master Edition  •  Version 2.0  •  October 2026
Theme: Smart & Sustainable Future   |   Focus: food-waste prevention, resource efficiency, climate impact
Team: [Team name]  |  [Member names]
Vasavi College of Engineering (Autonomous), Hyderabad
Covers: problem, evidence, landscape, features, architecture, data and pilot, ML methodology, evaluation,
impact, risks, roadmap, demo plan, judge Q&A, checklists and appendices.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 2
## Contents
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 51. Executive summary
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 51.1 What makes it original
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 51.2 What we will demonstrate
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 61.3 How it scores against the judging criteria
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 72. The problem
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 72.1 The scale of food waste
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 72.2 Why institutional kitchens waste food
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 72.3 Who is affected
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 72.4 Formal problem statement
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 82.5 Alignment with the hackathon theme
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 93. Existing solutions and the gap
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 9Our differentiators
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 104. The proposed solution
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 104.1 Vision
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 104.2 The closed loop
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 104.3 Product layers
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 104.4 Users and roles
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 114.5 User journeys
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 125. Feature catalogue
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 12Module A. Demand forecasting engine
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 12Module B. Cooking quantity planner and optimiser
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 13Module C. Waste measurement and capture
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 14Module D. Waste intelligence and root cause
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 14Module E. Savings proof
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 14Module F. Student and community engagement
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 14Module G. Food-safe surplus routing
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 15Module H. Sustainability and finance
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 15Module I. Platform, safety and governance
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 16Recommended “wow set” for the demo
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 16Build ladder (strict order)
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 176. System architecture
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 176.1 Technology choices and why
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 186.2 Service modules and API

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 3
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 186.3 Screens
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 196.4 Design principles
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 207. Data plan and pilot design
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 207.1 Data tables
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 207.2 Collection protocol
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 217.3 Measurement discipline
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 217.4 Pilot design
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 217.5 Data size, honestly
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 217.6 Synthetic data policy and generator
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 227.7 Ethics, permission and privacy
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 238. AI and machine-learning methodology
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 238.1 Headcount forecasting
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 238.2 Per-head consumption by dish, with shortage-aware learning
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 238.3 Quantity recommendation and optimiser
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 248.4 Uncertainty
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 248.5 Last-minute nowcast and top-up plan
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 248.6 Savings simulator and blind reveal
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 258.7 Plate- and bin-waste photo estimation
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 258.8 Voice logging
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 258.9 Anomaly detection and root-cause hypotheses
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 268.10 Explainability
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 268.11 Continuous learning and drift monitoring
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 268.12 Responsible AI
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 279. Evaluation framework
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 279.1 Metrics
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 279.2 Statistical treatment of the pilot
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 279.3 How the project maps to the judging criteria
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 2910. Impact analysis
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 2910.1 Four kinds of impact
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 2910.2 Impact calculator
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 2910.3 Scale of the opportunity: an arithmetic illustration
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 2910.4 Choosing an emission factor
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 3010.5 Scalability path
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 3010.6 Sustainability of the project itself
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 3111. Risks and mitigation
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 3212. Development roadmap

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 4
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 32If you have less time: a 10-day plan
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 33Definition of done for every feature
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 33Suggested team split (adapt to your size)
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 33Repository layout
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 33Testing and validation plan
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 3413. Demo and presentation plan
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 3413.1 Principles
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 3413.2 Five-minute demo script
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 3413.3 The 60-second pitch
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 3413.4 Pitch deck outline
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 3513.5 Anticipated judge questions
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 3714. Final deliverables and submission checklist
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 37Future expansion
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 38Appendix A. Data sheets
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 38Appendix B. Database schema (core tables)
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 38Appendix C. Formula cheat-sheet
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 39Appendix D. Permission checklist
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 39Appendix E. Glossary
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 39Appendix F. References to verify and cite
.  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  .  . 40Appendix G. Key design decisions

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 5
- Executive summary
Every mess cooks for hundreds of people, three or four times a day, without knowing how many will turn up
and without weighing what comes back. MessWise turns that guess into a measured, learning decision loop.
Hostel messes, college canteens, hospital kitchens and caterers decide, meal after meal, how much of every dish to cook.
Running short causes immediate complaints; wasting food is silent. So kitchens over-cook by habit. The cost is real: edible
food, ingredients, fuel, labour and money are binned, the emissions embedded in that food are wasted, and on other
days students still go short.
MessWise is a low-cost, explainable platform that closes the loop. It predicts the headcount for every meal, plans the
cooking quantity of every dish at a service level the manager controls, lets the kitchen measure leftovers in seconds
(form, voice or photo), and learns from each meal. Around that core it adds a counterfactual savings simulator, student
check-ins, food-safe surplus alerts for NGOs, and automatic cost, CO
## 2
e and SDG 12.3 reporting.
1.1 What makes it original
#IdeaWhy it matters
1Prevention first, rescue second. Plan the right quantity before
cooking; alert NGOs only about what is left, and only inside a
food-safety window.
Most Indian efforts act after food is cooked, when the
ingredients, fuel and emissions are already spent.
## 2
Shortage-aware consumption learning. A dish that ran out is
treated as a lower bound on appetite (right-censored), using
survival-analysis tools (Kaplan–Meier).
Naive averages learn that students want less than they were
able to get. This is the subtle error that makes mess plans
drift into shortages.
## 3
Cost-aware optimiser with a visible slider. A newsvendor model
turns “how bad is running out versus wasting a kg?” into a service
level per dish.
Staples (rice, roti) get 99%; sides get 90%. The trade-off
between surplus and run-out risk is shown, not hidden.
4Savings you can trust. A no-look-ahead simulator replays history;
a prediction log freezes every live forecast before the outcome; a
blind-reveal demo shows the model beating the baseline in front
of judges.
Proof, not promises. Pilot numbers and simulator estimates
are always kept apart.
## 5
Capture that cooks will actually use. Big-button form,
Telugu/Hindi/English voice logging with confirmation, calibrated
tray-photo estimate, optional ESP32 smart scale.
Logging discipline decides whether any kitchen AI works. We
attack the friction directly.
## 6
Built for Indian bulk cooking. Dishes in kg, litres and counts (rice,
dal, sabzi, curd, rotis), not restaurant plates or point-of-sale items.
Hostel students are on a monthly plan, so there is no
per-item billing to forecast from.
7People in the loop, privacy by design. The cook can override
every number (with a reason); only counts and kilograms are
stored; no names, IDs or faces.
Trust, safety and adoption. The model recommends; people
decide.
1.2 What we will demonstrate
•A forecast shown honestly next to a simple baseline (same meal, same weekday last week), with a one-sentence
explanation of its drivers.
•Per-dish cooking quantities with an adjustable service level and a visible probability of running out.
•A blind forecast reveal: pick a real past meal, hide the outcome, let MessWise forecast and plan, then reveal what
happened.
•Measured kilograms, rupees and CO
## 2
e saved from a real 2–3 week pilot at our own mess, each with its method and
assumptions on screen.
•A complete, working application with a recorded backup demo and ready answers for judges.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 6
The winning thesis
Not “we built an AI dashboard”, but “we measured the problem in a real mess, used those observations to make better
cooking decisions, measured what changed, and built a system that can repeat that anywhere.” An evidence-backed
intervention beats an ambitious mock-up. Every feature in this document exists to support that story.
1.3 How it scores against the judging criteria
CriterionOur edgeProof shown to judges
Innovation & originality
Prevention-first loop; censored consumption learning;
newsvendor service levels; blind-replay savings proof; Indic
voice capture.
Live slider, simulator, voice demo,
comparison slide.
AI / technical
implementation
Time-ordered validation vs two baselines; conformal
intervals; Monte-Carlo quantity optimiser; anomaly +
root-cause rules; speech and vision with fallbacks.
Model-vs-baseline chart, explanation
sentence, architecture diagram, API
docs.
Problem relevance &
impact
Real pilot at a real mess; kg, ₹, CO
## 2
e measured; SDG 12.3
alignment; service level protected; scale path to schools and
caterers.
Before/after numbers with sample size
and caveats; impact report PDF.
FunctionalityEvery dashboard element is computed from logged data;
core runs with no API keys; synthetic mode clearly labelled.
Full walk-through; recorded backup;
offline copy.
Presentation & demoA five-minute story from a real number to a measured
result; judges speak a leftover entry and move the slider.
Rehearsed script, deck, backup video.
Assumptions made while writing this document
(1) The team can get permission to run a pilot at one hostel mess or canteen. (2) The submission deadline is not fixed, so
the roadmap is a 4-week plan that can be compressed to about 10 days (section 12). (3) The stack stays in Python so a small
team can finish it. (4) The official problem statement is taken to be mess-waste forecasting under the “Smart & Sustainable
Future” theme. Replace anything that does not match your situation.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 7
- The problem
2.1 The scale of food waste
The UN Environment Programme’s Food Waste Index Report 2024 (with WRAP) estimates that about 1.05 billion tonnes
of food were wasted worldwide in 2022, close to one fifth of the food available to consumers. Roughly 60% came from
households, about 28% from food service (restaurants, canteens, catering) and about 12% from retail. For India, coverage
of the report puts household food waste at about 78 million tonnes a year, around 55 kg per person, second only to
China in total tonnage.
Be careful how these numbers are used
These are household figures. A hostel mess is a food-service operation and we do not rely on any published benchmark for
it. That is exactly why a measured pilot is the centre of this project: it creates a real baseline for one Indian institutional
kitchen. Distinguish food loss (supply chain) from food waste (retail, food service, households), and always say where a
number comes from.
2.2 Why institutional kitchens waste food
•Demand moves, quantities do not. Headcount shifts with exams, weather, holidays, events, menu popularity,
month-end and students eating outside. Cooking quantities rarely follow.
•The costs are lopsided. Running out causes immediate complaints; wasting food is silent. Cooks therefore over-cook
to stay safe.
•Nothing is measured. Without kilograms per dish per meal, nobody can see which dishes, days or meals waste the
most.
•Per-person consumption is guessed. How much rice or dal one student eats lives in an experienced cook’s head, not
in a record, and it differs by dish and meal.
•Dishes behave differently. A popular protein dish has a different demand curve from rice or a vegetable side, so one
headcount number is not a plan.
•Data is not turned into decisions. Registers and token counts may exist, but they are not linked to cooked quantity,
leftovers or cost.
•Safe surplus rarely moves in time. When food is left and still safe, there is little time or coordination to reach a
recovery partner.
2.3 Who is affected
StakeholderWhat they lose today
Mess contractor / managerIngredient, fuel and labour cost on food nobody eats; complaints on shortage days; no data to
defend or improve the menu.
StudentsQuality drops when quantities are mis-planned; shortages at the end of a meal; no voice in the
menu.
College / hostel administrationHard to report on sustainability; recurring complaints; no evidence for contract reviews.
## Environment
Food waste in landfill generates methane; the water, land and energy used to grow and cook it are
lost.
SocietyEdible food is binned while people nearby go hungry, because surplus seldom arrives in time and
safely.
2.4 Formal problem statement

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 8
Problem statement
Hostel messes and institutional kitchens cannot predict meal-wise demand or measure what they waste, so they cook by
habit: edible food, money and emissions are lost on over-cooking days while students face shortages on others. There is no
affordable, explainable, multilingual tool that predicts demand, recommends per-dish quantities at a controllable risk level,
measures waste with low effort, involves students, routes safe surplus onward and proves its effect with real kitchen data.
2.5 Alignment with the hackathon theme
Theme: Smart & Sustainable Future (waste management, resource efficiency, environmental challenges). The project
directly supports UN SDG 12.3 (halve per-capita food waste at retail and consumer level and reduce food losses along
production and supply chains by 2030), and contributes to SDG 13 (climate action, through avoided emissions) and SDG 2
(zero hunger, through safe surplus recovery).

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 9
- Existing solutions and the gap
Before building, we mapped what already exists. MessWise is designed to complement these tools, not to compete with
their strengths. Details come from our research and must be re-verified from each organisation’s own website before
they appear on a slide.
CategoryExamplesWhat they doGap for a hostel mess
Commercial kitchen
waste tracking
## Winnow, Leanpath
Smart scales and cameras record
what a professional kitchen
throws away and why.
Aimed at hotels and large food-service firms;
usually need installed hardware and paid
subscriptions; not built around hostel
headcount forecasting or Indian bulk dishes.
## Surplus
redistribution
## Robin Hood Army,
Feeding India, FSSAI’s
## Indian Food Sharing
Alliance network
Move cooked surplus to people
who need it.
Acts after the food is cooked, so cost, resources
and emissions are already spent; coordination is
manual and time-sensitive.
## Surplus
marketplaces
## Too Good To Go, Olio
Sell or share surplus from shops
and restaurants.
Retail-oriented and strongest outside India;
does not help a fixed-menu mess plan what to
cook.
Composting / biogas
Campus composters,
biogas units
Convert waste into compost or
energy.
Valuable, but treats waste that already exists
instead of preventing it.
Restaurant analyticsPOS-based forecasting
tools
Forecast sales per item from
billing data.
A mess has no per-item billing; students are on
a monthly plan, so demand must be inferred
from headcount and consumption.
Manual registersToken counts,
notebooks
Record attendance or tokens for
billing.
Not linked to cooking quantity or leftovers, so it
never becomes a decision.
Our differentiators
Gap in the marketHow MessWise fills it
Prevention, not only redistributionForecast, per-dish plan and service-level control before cooking; surplus alerts only for what
remains.
Fits fixed-menu bulk cooking
Learns kg-per-head per dish from (cooked − leftover) ÷ headcount and handles shortage days
correctly.
Low cost of adoptionA kitchen scale and a phone are enough; voice logging in Telugu, Hindi and English reduces
typing; optional ₹-level smart scale.
Students are ignoredOptional anonymous check-ins, ratings and an impact wall make students part of the solution.
Savings are rarely provenPilot before/after with matched meals, plus a simulator that replays history using only data
available at the time.
Black-box AI
Every forecast shows its drivers; the cook can override and the reason is logged; core features
work with no external AI service.
Donation as the main answerDonation is a controlled exception path with safety gates; the primary strategy is not creating
the surplus.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 10
- The proposed solution
## 4.1 Vision
Every institutional kitchen cooks what it will actually serve: no hungry students, no binned food, and a measurable record
of the food, money and carbon saved.
4.2 The closed loop
MessWise is a loop, not a report. Each meal produces data that makes the next meal’s plan better.
## 1  PREDICT
headcount for
every meal
## 2  PLAN
kg per dish at a
chosen service level
## 3  COOK
cook follows plan
or overrides (logged)
## 4  MEASURE
leftovers weighed,
shortages flagged
## 5  LEARN
rates + model
retrain, drift check
every meal makes the next meal’s plan better
## SAFE SURPLUS ALERT
only what is left, within the safe window
Figure 1. The MessWise decision loop. Surplus routing is a controlled exception path, not the main strategy.
4.3 Product layers
LayerPurposePrimary users
PredictionForecast headcount for every meal and the demand for every dish.Manager, cook
OptimisationTurn demand into a quantity that balances waste cost against shortage cost.Manager
MeasurementCapture cooked, served, leftover and shortage records with minimal effort
(form, voice, photo, scale).
Kitchen staff
IntelligenceExplain waste, flag anomalies, propose root causes, track cost and trends.Manager, administration
SustainabilityEstimate food, cost, CO
## 2
e and SDG 12.3 progress, always labelled as estimates
with method.
Administration, students
RecoveryFlag safe surplus and coordinate approved partners inside the safe window.Manager, NGO partner
LearningFeed outcomes back into rates and models; monitor drift; keep a prediction log.System, admin
Product principle: four questions
Every feature should answer one of four questions: prepare less, prepare better, waste less, or recover safe surplus. If a
feature answers none of them, it is cut.
4.4 Users and roles
RoleUses MessWise toMain screens
Cook / kitchen staffSee today’s plan, log cooked quantity and leftovers by form or voice,
request a top-up, note why waste happened.
Kitchen mode (large buttons,
local language)
Mess managerSet service levels, review forecasts and costs, accept or override
plans, approve surplus alerts, read the weekly brief.
Command center, planner,
procurement

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 11
RoleUses MessWise toMain screens
Warden / administrationTrack waste, savings, feedback and sustainability metrics; export
reports; compare messes.
Admin analytics, monthly impact
report
Sustainability officer /
auditor
Review methods, audit log and impact numbers; export data.Reports, audit log
StudentsCheck in (optional), rate dishes, see how much food the hostel
saved.
Check-in form, impact wall
NGO partner
Receive an advance surplus alert and confirm pickup inside the safe
window.
Pickup alerts
PublicSee aggregate impact only (read-only).Public impact dashboard
4.5 User journeys
JourneySteps
Manager, morning
1) Open Command Center. 2) Review today’s forecast, range and drivers. 3) Review per-dish quantities and
run-out risk. 4) Move the service level if needed. 5) Accept or override (reason recorded). 6) Print or share
the cooking plan and procurement list.
Cook, after the meal1) Open Kitchen mode. 2) Confirm cooked quantity per dish (one-tap copy of plan). 3) Enter leftovers by
number, voice or photo. 4) Flag any dish that ran out. 5) Pick a waste reason. 6) Confirm and submit; a
data-quality check runs instantly.
System, after
submission
1) Validate and store. 2) Update KPIs, waste %, cost. 3) Detect anomalies and draft root-cause hypotheses.
4) Update per-head rates (shortage-aware). 5) Compare the stored forecast with the outcome. 6) Queue
retraining; raise drift or data-quality alerts.
## Administration,
monthly
1) View waste and savings trend. 2) Compare hostels. 3) Review service level and model accuracy. 4)
Download the green-campus report. 5) Choose the next intervention.
Student1) Scan QR, tap Yes/No/Maybe for tomorrow. 2) Rate the meal in one tap. 3) See the impact wall.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 12
- Feature catalogue
Features are grouped into nine modules. Every feature carries a tier so the team always knows what to build first.
TierMeaningRule
P0MVP. Must work flawlessly in the demo.All P0 items are finished and tested before anything else.
P1Differentiator. Strong, buildable, high value.
Build in the order of the build ladder (end of this section); finish
each one fully.
P2Vision and roadmap.Shown on the roadmap slide; build only if time remains.
More features does not mean more half-working features
Judges score Functionality and Presentation as well as ambition. A smaller set that works end to end beats a long list of
buttons that do nothing. Fake or non-functional dashboard elements are the fastest way to lose trust. If a feature is not
built, it goes on the roadmap slide, not on the demo screen.
Module A. Demand forecasting engine
Python, pandas, scikit-learn (regularised linear model first; random forest or gradient boosting only if clearly better), time-ordered
validation. The simplest model that beats the baseline wins.
IDFeatureWhat it doesTier
## A1
Meal-wise headcount
forecast
Predicts headcount for every upcoming meal (breakfast, lunch, snacks, dinner) for the
next 1–7 days.
## P0
A2Honest baselines
Always shows the model beside “same meal, same weekday last week” and a trailing
weekday×meal average, so the gain is visible and real.
## P0
A3Participation-rate model
Forecasts the share of hostel strength that eats (headcount ÷ strength) and multiplies
by strength, so empty-hostel weeks and vacations are handled correctly.
## P0
A4Context features
Weekday, meal, menu tags, week of semester, holiday / exam / event flags, weather
(Open-Meteo), same-meal lag-7 and rolling mean.
## P0
A5Explainable forecasts
A plain sentence plus top drivers: “Higher than usual: Sunday, biryani on the menu,
rain expected.” Compared with the last three similar meals.
## P0
A6Uncertainty bandsAn 80% interval from split-conformal / rolling-error quantiles instead of one number;
low-confidence flag for unusual days.
## P0
A7Event and exam calendarAdmin marks events, fests, exam weeks and holidays; the model learns their effect.P1
A8Menu-popularity effectLearns which dishes pull students in or push them to eat outside.P1
A9Student check-in featureAggregate yes / no / maybe counts for tomorrow enter the model as a feature (never
names).
## P1
A10Last-minute nowcastUpdates the headcount forecast from early-service counts using the learned arrival
curve; narrows the interval as the meal unfolds.
## P1
A11Self-improving retraining
Weekly or on enough new rows; champion–challenger swap; rolling error and bias
tracked; drift alert; versioned model registry.
## P1
A12Advanced ensembleTime-series models (ETS / SARIMAX) blended with the regression model once
imported registers give 8+ weeks of history.
## P2
Module B. Cooking quantity planner and optimiser
Pure Python on top of the forecast; no external AI service is needed for any feature in this module.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 13
IDFeatureWhat it doesTier
B1Per-dish quantity plan
Turns forecast headcount into kilograms, litres or counts per dish, with a small
allowance for preparation loss and practical batch sizes.
## P0
B2Per-head consumption
learning
Learns how much of each dish one person is served from (cooked − leftover) ÷
headcount, using a robust median split by meal type.
## P0
B3Service-level slider
Manager picks how safe to be (for example 90 / 95 / 99% chance of not running out)
and sees expected surplus and run-out risk change live.
## P0
B4Cost-aware optimiserNewsvendor logic: service level derived from the cost of a short kg versus a wasted kg;
dish criticality tiers (staples 99%, sides 90%); manager can override.
## P1
B5Shortage-aware learningMeals where a dish ran out are right-censored lower bounds, handled with
Kaplan–Meier so the model never learns that students want less than they got.
## P1
B6Monte-Carlo demand
Combines headcount uncertainty and per-head rate uncertainty into one demand
distribution for each dish.
## P1
B7Top-up planCook a first batch plus a second batch triggered by the first-service count; late-meal
refill recommendation.
## P1
B8What-if planner
Change menu, add an event, set “what if 470 students attend?” or alter service level
and see new quantities and cost instantly.
## P1
B9Procurement listConverts dish plans into rice, dal, oil and vegetable quantities for the next 1–3 days
from manager-entered recipes.
## P1
B10Cost per plateUses manager-entered prices to show cost per plate and the cost of leftovers by dish.P1
B11Run-out risk alertWarns when the planned or overridden quantity has a high chance of falling short.P1
B12Inventory awarenessOpening / closing stock, low-stock warnings, substitution suggestions where the
manager permits.
## P2
B13Waste-aware menu
planning
Suggests menu tweaks from dish popularity and waste history.P2
Module C. Waste measurement and capture
Designed so a cook can finish a meal’s log in a couple of minutes, with quality checks running automatically.
IDFeatureWhat it doesTier
C1Fast leftover loggingBig-button form: for each dish, cooked quantity and leftover weight, with defaults and
one-tap copy of the plan or last meal.
## P0
C2Data-quality checksRejects impossible entries (leftover more than cooked), flags missing meals, unit
mix-ups (raw vs cooked weight) and outliers before they reach the model.
## P0
C3Waste taxonomyStage (preparation, serving surplus, plate waste) plus reason tags (overproduction,
low popularity, quality, timing, portioning, other).
## P1
C4Register / CSV importImports headcount registers or billing counts so the model has history from day one.P1
C5Voice loggingCook says “rice cooked 40 kg, left 6 kg” in Telugu, Hindi or English; speech-to-text plus
a rule-based parser fills the form; the cook confirms.
## P1
C6Calibrated photo estimate
Photo of the standard waste bin with a reference marker; fill level is converted to kg
through a scale-calibrated curve; confidence shown; manual fallback always available.
## P1
C7Timestamped entrance
tally
Counts at 15-minute buckets give the arrival curve used by the nowcast and top-up
plan.
## P1
C8Smart scaleESP32 + HX711 load-cell platform posts weights to the app; removes manual typing of
weights.
## P2
C9Offline-tolerant captureEntries queue locally if the network drops and sync later (progressive web app).P2

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 14
Module D. Waste intelligence and root cause
Plotly charts inside Streamlit; every number is computed from logged data and links back to its formula.
IDFeatureWhat it doesTier
D1KPI dashboardKg wasted, waste as % of cooked, rupees, meals served, forecast error, service level;
every number links to its formula.
## P0
D2Pattern chartsWaste by weekday, meal and dish; headcount trends; interactive Plotly charts.P0
D3Dish performance rankingMost-wasted and best-loved dishes with “rework or retire” suggestions.P0
D4Anomaly detectionFlags unusual waste spikes, attendance drops and entry errors using robust z-score or
IQR rules against each dish’s own history.
## P1
D5Root-cause hypothesesRule-based explanations (unpopular dish, forecast miss, over-cooking versus plan,
portion size, prep loss) drafted for manager review and labelled as hypotheses.
## P1
D6Override analytics
Every override records a reason; shows override rate and whether overrides beat or
lost to the recommendation.
## P1
D7Auto weekly briefPlain-language weekly summary; template by default, optional LLM polish; works with
no API key.
## P1
D8Ask MessWise
Questions such as “Which dish wasted most last week?” answered by safe pre-built
queries, optionally with an AI interpreter.
## P2
D9Cross-mess benchmarkingCompare blocks or messes on waste per person per meal.P2
Module E. Savings proof
The module that turns a prototype into evidence.
IDFeatureWhat it doesTier
E1Prediction log
Every live forecast and plan is stored with a timestamp before the outcome is known,
so accuracy can never be claimed with hindsight.
## P0
E2Pilot before/after reportMatched weekday×meal comparison, event days separated, bootstrap confidence
interval, service level and sample size shown.
## P0
E3Savings simulatorReplays past meals as if MessWise had planned them using only data available at the
time; reports food avoided, cost and shortage events.
## P1
E4Blind forecast revealPick a past meal, hide the actual result, generate forecast and plan, then reveal and
compare. Doubles as the demo centrepiece.
## P1
Module F. Student and community engagement
Everything student-facing is optional and anonymous; the platform works without it.
IDFeatureWhat it doesTier
F1Meal check-inOptional QR or link: “Eating tomorrow? Yes / No / Maybe.” Aggregate only; used as a
forecast feature.
## P1
F2One-tap meal ratingStudents rate the meal; ratings feed the dish-popularity model and root-cause rules.P1
F3Student impact wallPublic screen: kilograms saved this week, meals-equivalent, CO
## 2
e avoided.P1
F4Zero-waste streaksFloors or blocks earn points for early skip declarations and clean plates; aggregate and
fair by design.
## P2
F5Dish votingStudents vote on dishes to repeat or retire.P2
Module G. Food-safe surplus routing
Alerts only in the MVP; physically moving food needs a partner NGO and food-safety approval.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 15
IDFeatureWhat it doesTier
G1Predicted-surplus alert
“Expected 6–9 kg surplus around 8:45 PM” goes to the manager and, once approved,
to partner NGOs (in-app, Telegram, or a pre-filled WhatsApp click-to-chat link).
## P1
G2Food-safety clockTime and temperature log with hold-time cut-offs; the app refuses to propose
donation once the safe window has passed or if eligibility is not confirmed.
## P1
G3NGO directory and pickupsVerified partner list (FSSAI registration checked), pickup window and confirmation.P2
G4Donation recordQuantity, time, temperature and partner recorded in the fields the FSSAI surplus-food
regulations expect; certificate for CSR or green-audit use.
## P2
Safety rule
MessWise never recommends re-serving cooked leftovers. Only food flagged eligible can enter the donation workflow;
food with uncertain history, suspected contamination or an expired window is blocked. Surplus handling follows FSSAI and
local guidelines, which the team must confirm and cite before demonstrating this module. The app provides reminders and
documentation; it does not replace food-safety professionals.
Module H. Sustainability and finance
Estimates are always labelled as estimates, with method and source.
IDFeatureWhat it doesTier
## H1CO
## 2
e estimate
Kilograms avoided × a cited emission factor, shown as a low / central / high band and
labelled an estimate.
## P1
H2Meals-equivalent“Enough food for N meals” computed from learned per-head consumption.P1
H3SDG 12.3 trackerWaste per person per meal against the pilot baseline, with progress over time.P1
H4Green-campus reportOne-click monthly PDF for the administration with charts, method and assumptions.P1
H5Water and energy
footprint
Estimated water and energy embedded in the food saved, only where a defensible
factor exists.
## P2
H6Budget vs actualFood-cost utilisation against the mess budget.P2
Module I. Platform, safety and governance
Cross-cutting features that keep the system private, safe and dependable.
IDFeatureWhat it doesTier
I1Privacy by design
No names, IDs, phone numbers or faces. Only aggregate counts and kitchen quantities
are stored.
## P0
I2Human in the loopThe model recommends; staff decide. It never silently changes a production quantity.
Overrides are logged with a reason.
## P0
I3Works without AI keysAll core features run locally; AI services only add optional text, speech or vision, each
with a fallback.
## P0
I4Synthetic demo modeGenerated data for development and demo, always labelled “synthetic” and never
shown as pilot results.
## P0
I5Role-based viewsCook, manager, admin, auditor, student and NGO each see only what they need.P1
I6Audit log and export
Every entry, override and model version is logged; export to CSV and PDF; deletion per
institutional policy.
## P1
I7Multi-mess support
Separate boys’ and girls’ hostels and canteens with their own models and shared
reporting.
## P1
I8Multilingual interfaceEnglish, Telugu and Hindi labels for kitchen-facing screens.P1

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 16
IDFeatureWhat it doesTier
I9NotificationsForecast ready, high uncertainty, over-production risk, low stock, waste spike, safe
surplus, missing-log reminder, model-performance warning.
## P1
I10Forecast APIFastAPI service (/forecast, /plan, /simulate, /log) with auto-generated docs so
attendance or ERP systems can integrate later.
## P1
Recommended “wow set” for the demo
•E4 + E3 Blind reveal and savings simulator: a live replay that shows what the data would have saved, with shortages
counted honestly.
•B3 + B4 Service-level slider with cost logic: the room sees waste and run-out risk trade off in real time.
•C5 Voice logging: a judge speaks a leftover entry in Telugu and it fills the form.
•G1 + G2 Surplus alert with a safety clock: responsible handling, not just a donate button.
•H4 Impact report: a printed or on-screen report with kilograms, rupees and CO
## 2
e, method shown.
•Bonus, only if everything else is done: C8 smart scale weighing a bucket live and filling the form.
Build ladder (strict order)
StepBuildDone when
1I4 synthetic data, C1 + C2 logging with validation, I1 privacy rulesA meal can be logged, rejected if impossible, and stored.
## 2
A1–A6 forecast with baselines, explanation and intervals; E1
prediction log
Forecast page shows model vs baseline with a range and
a sentence.
3B1–B3 per-dish rates, quantity plan and sliderPlan page shows kg per dish, expected surplus and
run-out risk.
4D1–D3 dashboards; E2 pilot reportEvery number traces to logged data.
5E3 + E4 simulator and blind revealA past meal can be replayed with no look-ahead.
6B4 + B5 cost-aware and shortage-aware logicRan-out meals are handled as lower bounds; costs set the
service level.
7G1 + G2 surplus alert with safety clockAlert is blocked once the safe window passes.
8C5 voice logging; H1 + H2 + H4 impact and reportVoice fills the form; the PDF report generates.
9Everything else in P1 by value; then P2Only if steps 1–8 are solid.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 17
- System architecture
Five layers keep the system simple to build and easy to explain. Every box in the diagram is a real module in the code
base, not just a drawing.
## 1  CAPTURE
Cook form
(per meal)
Voice log
## Te / Hi / En
Tray / bin photo
+ marker
Entrance tally
## (timestamped)
Student check-in
+ rating (opt.)
Register CSV,
weather, calendar
## 2  DATA
## Validation +
quality checks
SQLite / Postgres
store
Privacy filter
(counts only)
Prediction log +
audit log
Synthetic data
## (labelled)
## 3  INTELLIGENCE
## Headcount
forecaster
Per-dish rate
learner (censored)
## Cost-aware
quantity optimiser
Savings simulator
+ blind replay
## Anomaly +
root-cause rules
## 4  SERVICES + APP
Python core package  (messwise/)
FastAPI
## /forecast /plan /simulate
Streamlit app: Kitchen mode, Planner, Forecast lab,
Simulator, Waste intelligence, Impact, Reports
## 5  OUTPUTS
## Cooking
plan
## Procurement
list
Surplus alert +
safety clock
## Weekly
brief
Impact report
## (PDF)
Public impact
wall
CROSS-CUTTING:  role-based access  ·  human override with reason  ·  audit trail  ·  works with no AI keys  ·  estimates labelled
Figure 2. Five-layer architecture. The same Python core package serves both the Streamlit app and the FastAPI service.
6.1 Technology choices and why
ComponentChoiceWhyUpgrade path
Language and
data
Python 3.11, pandas, NumPy
Familiar, fast for tabular data, one language
end to end.
## –
## Machine
learning
scikit-learn (Ridge / ElasticNet,
random forest, gradient boosting),
statsmodels, lifelines
(Kaplan–Meier), joblib
Reliable on small data; easy to explain;
models saved and reloaded.
XGBoost / LightGBM,
Bayesian hierarchical model
when data grows.
Core package
messwise/ (forecast, rates,
optimiser, simulator, validation)
One tested code base reused by the UI and
the API; no duplicated logic.
Packaged as an internal
library.
## API
FastAPI + Pydantic, auto docs at
## /docs
Shows an API-first, integrable product for
ERP / attendance systems; input validation
for free.
Auth, rate limits,
multi-tenant.
Web appStreamlit + Plotly with custom
theme and large-button kitchen
mode
Fastest route to a working, reliable,
demo-ready product for a small team.
Functionality and demo stability beat
framework fashion.
React / Next.js front end
calling the same API; React
Native kitchen app.
## Storage
SQLite through SQLAlchemy; CSV
import / export
No server to manage; data stays on the
college machine; schema is
## Postgres-compatible.
Managed PostgreSQL (e.g.
## Supabase / Neon / Render)
and object storage for images.
WeatherOpen-Meteo API (free, no key for
basic use)
Forecast and history for the Hyderabad
area.
Cache locally; fall back to
no-weather model.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 18
ComponentChoiceWhyUpgrade path
## Speech
## (optional)
Streamlit audio input + Whisper
(runs locally) or a hosted
Indic-language speech-to-text API
Telugu / Hindi / English with
code-switching; falls back to typing. Test on
real kitchen noise and pick the best.
Fine-tuned Indic speech
model.
## Vision
## (optional)
OpenCV + fill-level model
(vision-capable LLM API or small
## CNN)
Standard bin with marker makes a narrow,
testable problem; always calibrated against
the scale.
Dish recognition; smart-bin
load cells.
Text generation
## (optional)
An LLM APIOnly for polishing weekly briefs and
optional Q&A; template fallback with no
key.
## –
AlertsIn-app, Telegram bot, WhatsApp
click-to-chat link
Free, instant and familiar; no WhatsApp
Business approval needed for the demo.
WhatsApp Business API /
## SMS.
## Reports
ReportLab or WeasyPrint PDFs;
Plotly static charts
One-click monthly green-campus report.Scheduled email delivery.
HostingStreamlit Community Cloud or
Render for the live demo; local
offline copy
Public link for judges plus a copy that works
with no internet.
Vercel + Render / cloud
container.
Qualitypytest, Git + GitHub with issues
board, README
Tests protect the maths; commit history
shows judges the work is real.
CI via GitHub Actions.
6.2 Service modules and API
ModuleResponsibilityEndpoint / entry point
Meal serviceMenus, meal records, dish records, quantitiesPOST /log/meal, POST /log/dish
Forecast serviceHeadcount forecast, interval, drivers, nowcastGET /forecast?date&meal
Optimisation serviceQuantities, service level, run-out risk, top-upPOST /plan
Waste serviceWaste records, voice and photo parsing results
POST /log/waste, POST /voice/parse,
POST /photo/estimate
Simulation serviceCounterfactual replay and blind revealPOST /simulate
Analytics serviceKPIs, anomalies, root-cause hypotheses, reportsGET /kpi, GET /report/monthly
Recovery serviceSurplus eligibility, safety clock, partner alertsPOST /surplus/alert
Model serviceTraining, registry, drift checksCLI: python -m messwise.train
## 6.3 Screens
ScreenKey components
Command CenterToday’s forecast, range, recommendation, run-out risk, alerts, savings so far.
Meal PlannerMenu, expected headcount, per-dish quantities, service-level slider, accept or override with reason.
Kitchen ModeLarge actions: cooked, served, leftover, ran-out, photo, voice, weight; local-language labels.
Forecast LabHistory, forecast vs baselines, intervals, what-if scenarios, blind reveal.
Savings SimulatorReplay controls, food avoided, cost, shortage events, assumptions panel.
Waste IntelligenceDish-wise waste, trends, reasons, anomalies, root-cause hypotheses.
Inventory and
## Procurement
Recipes, stock, ingredient list for the next 1–3 days, cost per plate.
Surplus and RecoveryEligible surplus, safety clock, partner alert, pickup status, donation record.
ImpactStudent wall, kg saved, ₹ saved, CO
## 2
e band, meals-equivalent, SDG 12.3 tracker.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 19
ScreenKey components
Reports and SettingsDaily, weekly, monthly reports and export; users, roles, menus, thresholds, safety configuration.
6.4 Design principles
•Explainable: a cook or judge can see why a number was recommended, with inputs, formula and uncertainty.
•Human override: recommendations are advice; the cook can change them and the change and its reason are logged.
•Graceful fallback: if the internet, speech service or AI key fails, the app still works.
•Privacy first: only counts and kilograms are stored.
•Measured, not assumed: every claim on a dashboard is computed from logged data.
•Honest interface: prediction, actual measurement and manual override are visually distinct; no green “success” colour
when uncertainty is high; charts only where they support a decision.
•Kitchen-first: minimal typing, large touch targets, high readability, usable on a phone with wet or gloved hands.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 20
- Data plan and pilot design
The project is built around real operational data from a pilot mess. Data quality matters more than model complexity: a
plain model on clean, consistent measurements beats a fancy model on messy ones.
7.1 Data tables
TableKey fieldsSource
meals
date, meal type, headcount, hostel strength, event / exam / holiday flags,
temperature, rain, source (tally or register)
Entrance tally, register,
Open-Meteo, calendar
menudate, meal type, dish list, tags (non-veg, sweet, festival special)Published weekly menu
dishesdish id, name, unit (kg, L, count), standard portion, prep-loss %, criticality
tier, recipe mapping
Manager, one-time setup
dish_log
date, meal type, dish, cooked qty, leftover qty, ran-out flag, waste stage,
reason tag, entry method (form / voice / photo / scale)
Cook form, voice log, kitchen scale
arrivalsdate, meal type, 15-minute bucket, cumulative countTimestamped tally app
checkins, ratingsdate, meal type, aggregate yes / no / maybe counts; aggregate rating
counts
Student form (optional)
costsdish or ingredient, cost per kg or litre, effective dateManager
eventsdate range, type (fest, exam, holiday), expected effect, notesAdmin
predictionscreated-at, target meal, model version, features snapshot, forecast +
interval, planned quantity per dish, service level, actual outcome (filled
later)
System (the prediction log)
overridestimestamp, role, dish, recommended qty, final qty, reasonPlanner screen
surplus_eventstimestamp, dish, estimated qty, eligibility, cooked time, temperature log,
partner, pickup status
Cook, manager, NGO
tray_photos
## (optional)
photo reference, bin id, estimated fill, scale weight, corrected valuePhone camera, scale
inventory (P2)ingredient, opening stock, received, used, closing stock, unit costManager
audit_logwho, what, when, old value, new valueSystem
7.2 Collection protocol
•Headcount: ask for the mess register or token counts first. If none exist, count at the entrance with a tally app that
timestamps taps, for the whole pilot. Optionally add an evening poll.
•Quantity cooked: one-page sheet filled by the cook per meal (kg of rice, litres of dal, count of rotis); the app replaces
the sheet once logging is stable.
•Leftovers: weigh leftover per dish at the end of service with a cheap kitchen scale and a pre-weighed (tared) bucket.
Note any dish that ran out and at what time.
•Menu and calendar: copy the published weekly menu; tag each dish; record exams, events and holidays the day they
are announced.
•Weather: download from Open-Meteo for each date automatically.
•Optional: plate-waste observation on a sample of trays, entrance-time buckets, student ratings.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 21
Suggested daily record (one meal)
Date 2026-10-14 · Meal: Lunch · Menu: rice, dal, chicken curry, salad · Expected headcount 430 (forecast) · Actual
headcount 417 · Rice cooked 55 kg, leftover 12 kg · Curry cooked 28 kg, leftover 4 kg · Ran out: none · Weather: rain, 24 °C ·
Event: mid-sem exam · Reason: overproduction (rice) · Entry: voice. (Illustrative format only. These are not measured
values.)
7.3 Measurement discipline
•Use the same scale and the same containers throughout; tare the container every time.
•Record the unit every time. Never mix cooked-weight and raw-weight measurements; MessWise works in cooked,
as-served weight.
•Timestamp every record and document unusual events (power cut, guest group, festival).
•Keep a data dictionary so future team members interpret fields the same way.
•Distinguish three waste stages: preparation (trim and cooking loss), serving surplus (cooked, never served) and plate
waste (served, not eaten). Planning uses served-per-head; plate waste guides portion size.
•Never edit measurements after the fact to make results look better. A credible pilot with a modest improvement beats
an invented dramatic one.
7.4 Pilot design
PhaseDurationWhat happensWhy
- Permission and
setup
2–3 days
Written permission, agreed data fields, scale and buckets,
tally app, staff briefing (one or two cooks trained), data
sheets, repository.
No permission, no pilot.
Logging must start
immediately.
## 1. Baseline
7–14 days (10+
preferred)
Kitchen cooks exactly as usual; we only log headcount,
cooked, leftover, ran-out and events.
Gives the “before” waste per
meal and per dish.
- Assisted pilotAbout 14 days
Week A: MessWise recommends quantities for the 3–4
highest-waste dishes at lunch and dinner. Week B: all dishes.
Manager approval mandatory; cook follows or overrides
with a reason; logging continues unchanged.
Gives the “after” numbers
while limiting risk; override
data shows trust.
- Analysis2–3 daysCompare matched weekday×meal; report event days
separately; report shortage incidents, override rate and
caveats.
Reduces confounders;
produces the impact
numbers.
Confounders and how we handle them
Exam weeks, holidays, festivals and menu changes can alter waste by themselves. Compare like with like (same weekday
and meal), report event days separately, record operational changes, and if a second mess block exists, treat it as a control
that receives no recommendations (difference-in-differences). Never attribute every change to the model without
evidence.
7.5 Data size, honestly
Lunch and dinner for 21 days give 42 meal rows (63 with breakfast, 84 with snacks), each with several dishes. This is small.
For that reason we use simple models, time-ordered validation, clear baselines and uncertainty-aware reporting. The
strongest value is the measurement and the per-dish consumption learning, which need few rows. If registers can be
imported, history grows quickly and richer models become justified. Decision: log lunch and dinner fully (highest volume
and variability); log breakfast and snacks at headcount level plus the main dish.
7.6 Synthetic data policy and generator
A generator creates realistic fake data for development and for a demo mode that works before the pilot ends. It is
always labelled synthetic, is never mixed into pilot results, and is never presented as evidence of savings.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 22
•Ground truth is known. The generator uses explicit parameters: base participation by weekday and meal, exam dip,
rain effect, menu-pull effect, per-dish appetite distributions, random noise and occasional shortages.
•It doubles as a unit test. Because the true parameters are known, we can check that the forecaster, rate learner
(including censoring) and simulator recover them. This is a strong technical-credibility point.
•It stress-tests the system: sudden holidays, a missing day of logs, a mistyped weight, an unusually large event.
•It is visibly watermarked on every screen and every export while active.
7.7 Ethics, permission and privacy
•Written permission from the mess contractor and warden; a faculty mentor’s letter helps.
•Collect counts and quantities only: no student names, IDs or phone numbers. Check-ins are anonymous and
aggregated.
•Photograph bins and trays, never faces; delete raw photos after the estimate is computed unless consent is given.
•Do not use attendance data for any unrelated monitoring. Aggregate or anonymise everything shown publicly.
•Share results with the mess first. Present it as help to cut cost and complaints, not as an inspection.
•Allow deletion and export according to institutional policy.
If permission is refused
Try a smaller canteen or cafeteria, run an opt-in check-in on a single hostel floor, import historical registers, or use clearly
labelled synthetic data for the models and describe the real-world pilot as planned future work. Say so plainly; do not blur
the line.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 23
- AI and machine-learning methodology
Principle: begin with interpretable baselines, add complexity only when real data justifies it, and report every result with
its uncertainty.
8.1 Headcount forecasting
Target. Number of students eating a given meal, modelled as H = S × p, where S is hostel strength (aggregate in-hostel
count from the administration) and p is the participation rate. Modelling p instead of H keeps empty-hostel weeks and
vacations from being mistaken for low appetite.
Features. Weekday, meal type, week of semester, holiday / exam / event flags, day after holiday, hostel strength, menu
tags, temperature and rainfall, headcount for the same meal one week earlier, rolling mean of the last four same-meal
days, and optional aggregate check-in counts.
Model ladderPurpose
Baseline 1: same meal, same weekday last weekThe simple benchmark every model must beat.
Baseline 2: trailing average by weekday and mealA stronger benchmark that smooths noise.
Regularised linear (Ridge / ElasticNet) on participation rateStable on small data; coefficients are easy to explain. Default model.
Random forest / gradient boostingCaptures interactions such as event × weekday; used only if it clearly
beats the linear model on time-ordered tests.
Ensemble with ETS / SARIMAX (P2)For mature histories (8+ weeks); weights set by recent error.
Validation. Expanding-window (rolling-origin) splits: train on the past, test on the next days; never random shuffles.
Metrics. MAE, WAPE = Σ|y − ŷ| ÷ Σy, and bias = Σ(ŷ − y) ÷ Σy. The final model is the simplest one that is clearly better than
both baselines; if none is, we say so and the planner still runs on the baseline plus a safety margin.
8.2 Per-head consumption by dish, with shortage-aware learning
For dish d and past meal i: r
d,i
## = (served
d,i
## ) ÷ H
i
, where served = cooked − leftover. The planner uses a robust estimate
over recent meals (default last 10), split by meal type. Plate waste is kept separate, because the kitchen must cook what
is served.
The hidden trap. If a dish ran out, (cooked − 0) ÷ H is only a lower bound on what students wanted. Averaging it in
teaches the model that students want less, which causes more shortages next time. We treat such meals as
right-censored observations: exact when there was leftover, a lower bound when the dish ran out. The Kaplan–Meier
estimator, standard in medical survival analysis, then gives an unbiased estimate of the appetite distribution.
# per dish d, meal type m  (last N meals)
rate      = served / headcount                 # kg per head
exact     = ~ran_out                           # False => right-censored lower bound
km        = KaplanMeierFitter().fit(rate, event_observed=exact)
r_q       = km.percentile(1 - q)               # q-quantile of appetite per head
# fallback when censoring is heavy or n < 6: median(uncensored) * (1 + bump), bump from history
8.3 Quantity recommendation and optimiser
Explainable core formula. Quantity
d
## = H
q
× r
d
× (1 + prep_loss), where H
q
is the q-th percentile of forecast headcount and
q is the service level chosen by the manager. This is what the planner shows first, because a cook can follow it.
Better estimate (default engine). Demand for a dish is the product of two uncertain things: headcount and appetite. A
Monte-Carlo draw combines both, so the plan reflects both uncertainties instead of only the headcount.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 24
H = H_hat + resample(conformal_residuals[meal_type], n=5000)   # headcount draws
r = draw(appetite_distribution[dish, meal_type],       n=5000)  # per-head appetite draws
D = H * r                                                      # demand for this dish
Q = quantile(D, q_dish) * (1 + prep_loss)                      # cook quantity
Q = round_to_batch(Q, pot_or_tray_size)                        # practical batch size
P_runout  = mean(D > Q / (1 + prep_loss));  E_surplus = mean(max(Q/(1+prep_loss) - D, 0))
Where does q come from? Either from the slider, or from a cost trade-off (the newsvendor model). If cooking one extra
kilogram that gets wasted costs C
o
(ingredients, fuel, labour, no salvage because leftovers are never re-served), and being
one kilogram short costs C
u
(emergency cooking, complaints, dissatisfaction), the cost-minimising service level is:
Newsvendor service level
q* = C
u
## ÷ (C
u
## + C
o
). The manager sets k = C
u
## ÷ C
o
(“how many times worse is running out than wasting a kg?”). Examples: k
= 4 gives q* = 80%; k = 9 gives 90%; k = 19 gives 95%; k = 49 gives 98%; k = 99 gives 99%. Dish criticality tiers set defaults:
staples (rice, roti) k = 99, main curries k = 19, sides and salads k = 9. A floor on q (default 90%) stops the system from ever
recommending a risky quantity.
Figure 3. Why the slider matters (illustrative, not pilot data). Moving from a 90% to a 99% service level costs only a few percentage points
of extra expected surplus but cuts the chance of running out ten-fold. The numbers depend on how variable demand is, which the pilot will
measure.
## 8.4 Uncertainty
Intervals come from split-conformal prediction: the signed residuals of past rolling-origin forecasts, stratified by meal
type, are used to place an 80% band around each new forecast. This needs no distributional assumptions and works on
small data. Coverage (how often actuals land inside the band) is tracked and reported. Days with unusual context (first
day after a holiday, an event, features outside the training range) or an unusually wide band receive a low-confidence
flag, and the planner suggests a higher service level or a top-up plan for those meals.
8.5 Last-minute nowcast and top-up plan
From timestamped entrance counts we learn the arrival curve a(τ): the fraction of the meal’s total headcount that has
arrived τ minutes after service starts. At a checkpoint τ
## 0
with n students counted, the nowcast is H
now
= n ÷ a(τ
## 0
). It is
combined with the prior forecast by inverse-variance weighting, and the interval narrows. Progressive cooking: for dishes
that can be cooked quickly, batch 1 is planned at a lower service level (for example 75–80%) and batch 2 = max(0,
## Q
updated
− batch 1). A guard prevents triggering on very small early counts.
8.6 Savings simulator and blind reveal
For every historical meal after a warm-up period, the simulator trains on data strictly before that meal, produces the plan
MessWise would have made, and compares it with what was actually consumed. There is no look-ahead.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 25
for meal i in time order (after warm-up):
fit forecaster + rates on data before i ;  plan_i = optimiser(service_level)
covered  = plan_i >= actual_consumption_i          # lower bound if the dish ran out
avoided  = max(cooked_i - plan_i, 0)   if covered and not ran_out_i
shortage = max(actual_i - plan_i, 0)   if not covered
report: kg avoided, rupees, shortage events and kg, bootstrap CI over meals, assumptions panel
Meals where a dish actually ran out cannot be verified and are reported separately instead of being counted as savings.
The simulator result is always labelled an estimate, separate from the measured pilot. Blind reveal runs the same
function on a single past meal with the actual hidden, then reveals it, so the audience watches the model forecast, plan
and be checked.
8.7 Plate- and bin-waste photo estimation
The camera is a measurement assistant, not a promise of exact kilograms from any photo. The workflow narrows the
problem so it can be validated:
•Leftovers go into a standard collection container of known geometry, with a reference marker visible in the frame.
•The model estimates a fill level (a volume proxy) and, where useful, which of the day’s few menu dishes it is.
•A calibration curve converts fill level to kilograms per food type, fitted on paired photo + scale measurements.
•The cook sees the estimate with a confidence score and confirms or corrects it. Corrected values become labelled
training data.
•During the pilot a subset is weighed to measure accuracy (MAE / MAPE), reported honestly. We claim accuracy only
for our container, lighting and food categories.
•If confidence is low, the app immediately falls back to manual weight entry.
8.8 Voice logging
Speech-to-text (Telugu, Hindi, English, with code-switching) produces a transcript; a rule-based parser extracts dish,
cooked and leftover quantities and units; the cook sees the filled form and taps to confirm. Nothing is saved without
confirmation.
StepWhat happens
- CaptureStreamlit audio input records a short clip; speech-to-text returns a transcript.
- NormaliseConvert number words and digits (including Telugu and Hindi number words), unify units (kilo, kg, litre, count),
lowercase and transliterate.
- Match dishes
Fuzzy-match words against today’s menu and a synonym lexicon (annam / chawal / rice, pappu / dal, perugu /
curd, kura / curry).
- Slot-fillRules link each quantity to a dish and to a role: cooked (cooked, vandamu, bana) or leftover (left, migilindi,
bacha).
- ConfirmPre-filled form with confidence; the cook edits and confirms. Failures fall back to typing.
Example utterances: “rice cooked 40 kg, left 6 kg”; Hindi: “chawal 40 kilo bana, 6 kilo bacha”; Telugu (transliterated): “annam 40 kilolu
vandamu, 6 kilolu migilindi”. Have a Telugu-speaking teammate verify phrasing and collect 30–50 real test utterances in the kitchen to
measure field-level accuracy.
8.9 Anomaly detection and root-cause hypotheses
Waste percentage per dish and meal is compared with its own history using a robust z-score, z = 0.6745 × (x − median) ÷
MAD, flagging |z| > 3.5, or an IQR rule; at least six past observations are required, otherwise the dish is marked
“insufficient history”. Flagged events are then run through transparent rules that draft hypotheses for the manager to
review:
Pattern observedHypothesis shownSuggested action
High leftover on all dishes + headcount far below
forecast
Attendance shortfall (forecast miss or
unlogged event)
Check event calendar; widen interval
for similar days.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 26
Pattern observedHypothesis shownSuggested action
High leftover on one dish + low rating + low
per-head rate
Dish is unpopular
Rework or retire; reduce quantity for
that dish.
Cooked quantity well above plan + high leftoverOver-cooking versus recommendation
## (override)
Review override reason; share the
cost of the override.
Leftover mostly at plate stagePortion size too large
Adjust serving spoon or offer a half
portion.
Preparation waste high for one dishTrim or process lossReview recipe yield and vendor
quality.
Dish ran out + headcount above upper bandUnexpected surge
Use top-up plan; log the cause for the
event calendar.
Waste spike on a day after a holidayReturn-pattern effectFlag as low-confidence day next time.
## 8.10 Explainability
•For the linear model, each feature’s contribution is its coefficient times its deviation from a typical day; the top three
drivers feed a sentence template, so the explanation is faithful to the model. For tree models, permutation
importance is used instead.
•Each forecast is shown next to the last three similar meals (same weekday and meal type, similar flags) with their
actual outcomes.
•Every recommendation shows inputs, formula, uncertainty and the reason for any increase or decrease versus last
time.
8.11 Continuous learning and drift monitoring
•Retraining: weekly or when enough new rows arrive. A new “challenger” model replaces the “champion” only if it
beats it on recent rolling-origin evaluation.
•Model registry: every version stores date, features, training window, metrics and baseline metrics; roll back in one
click.
•Prediction log: forecast and plan are stored before the outcome, so accuracy is never judged with hindsight.
•Drift alerts: rolling 14-day WAPE worse than the baseline, bias beyond a set limit for five consecutive meals, or feature
values outside the training range.
8.12 Responsible AI
•AI never acts alone: it recommends; the cook and manager decide, and the model never silently changes a production
quantity.
•No personal data is collected, so there is nothing to leak or misuse; attendance data is not used for unrelated
monitoring.
•Estimates (simulator, CO
## 2
e, photo estimates) are labelled as estimates with method and source.
•Every optional AI service has a non-AI fallback, and every dashboard element is computed from logged data.
•Reduction in waste that causes shortages is not success. Service level is reported next to every savings number.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 27
- Evaluation framework
A winning project measures both model performance and real operational impact, and is candid about what it could and
could not show.
## 9.1 Metrics
MetricDefinitionHow it is measuredDirection
Forecast errorWAPE, MAE and bias of headcount forecast
versus both baselines
Time-ordered test on pilot dataLower
Interval coverageShare of actuals inside the 80% bandPrediction logAbout 80%
Waste rateLeftover kg ÷ cooked kg, overall and per dishScale logs; baseline vs assisted
period
## Lower
Waste per meal / per
head
Leftover kg per meal and per person per mealScale logs, headcountLower
Service level achieved1 − (dish-meals that ran out ÷ all dish-meals)Ran-out flag in the cook formNot worse than
baseline
Shortage incidentsCount of meals or dishes that ran outRan-out flagNot higher
Avoidable costAvoided kg × ingredient cost per kgManager-entered pricesHigher saving
## CO
## 2
e avoided
Avoided kg × cited emission factor (low / central /
high)
Estimate with source shownHigher
Meals-equivalentAvoided kg ÷ per-head consumptionLearned consumption ratesHigher
Override rateShare of recommendations changed by staff;
outcome of overrides
Overrides tableFalls as trust
grows
Photo accuracyMAE / MAPE of fill-based estimate versus scaleWeighed sample of binsLower
Voice accuracyFields correct ÷ fields spoken on test utterances30–50 recorded kitchen utterancesHigher
Staff adoptionPercent of meals logged; minutes spent per mealLog completeness; stopwatchHigher / lower
Student satisfactionShort 1–5 survey before and afterAnonymous formNot worse
Recovery rateEligible surplus actually recoveredSurplus events (if partner active)Higher
The most important pilot metric
Change in waste per meal while maintaining service level. A reduction that causes shortages is not a success. No target
numbers are promised in advance; the pilot decides what is true, and the report states the measured change, the number
of meals behind it and the caveats.
9.2 Statistical treatment of the pilot
•Compare matched weekday×meal pairs between baseline and assisted weeks; report event days separately.
•With few observations, report a bootstrap confidence interval for the mean difference and, where suitable, a paired
Wilcoxon signed-rank test. Show n next to every number.
•If a control block exists, report a difference-in-differences estimate.
•Report the error distribution, not a single accuracy number, and keep the measurement procedure identical across
phases.
•State limitations plainly: short pilot, one site, season, concurrent events.
9.3 How the project maps to the judging criteria

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 28
CriterionWhat judges look forWhat we showRehearsal tip
Innovation and
originality
A fresh idea, not
another dashboard.
Prevention-first loop; censored consumption
learning; newsvendor slider; blind-replay proof;
Indic voice capture; optional smart scale.
Open with the gap sentence,
then show the slider within
90 seconds.
AI / technical
implementation
Right method for the
data; rigour; working
models.
Rolling-origin validation vs two baselines; conformal
intervals; Monte-Carlo optimiser; anomaly and
root-cause logic; speech and vision with calibration
and fallbacks.
Have the model-vs-baseline
chart and the architecture
figure one click away.
Problem relevance
and impact
Real problem, real data,
measurable benefit.
Pilot at a real mess; kg, ₹, CO
## 2
e with method; SDG
12.3; service level protected; scale path.
Lead with a real number
from the pilot; show sample
size.
## Functionality
It works, end to end,
without hand-holding.
Every element backed by real or labelled synthetic
data; core works without API keys; backup demo
and offline copy.
Rehearse the full
run-through twice without
help.
Presentation and
demo
Clear story, confident
delivery, interaction.
Five-minute narrative; judge speaks an entry; judge
moves the slider; clean slides; printed impact
report.
Assign speaker roles;
practise handling a failure
gracefully.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 29
- Impact analysis
10.1 Four kinds of impact
ImpactHow MessWise creates it
EnvironmentalLess food produced, cooked and discarded; less landfill methane; estimated CO
## 2
e (and, where defensible,
water and energy) avoided.
## Economic
Lower ingredient, fuel and labour cost; fewer emergency purchases; cost per plate and cost of leftovers
become visible; evidence for contract reviews.
SocialFewer shortages for students; safe surplus offered to people in need; students see and share the benefit.
EducationalA live campus example of data science for sustainability; students can contribute and learn from it.
10.2 Impact calculator
These formulas are computed by the app from logged data. The right-hand column is filled from the pilot, never from
guesses.
QuantityFormulaPilot value
Food avoided per mealBaseline average leftover kg − assisted average leftover kg (matched
meals)
[fill after pilot]
Food avoided per monthFood avoided per meal × meals per month[fill]
Cost saved per month (₹)Food avoided per month × average ingredient cost per kg[fill]
## CO
## 2
e avoided per monthFood avoided per month × emission factor (cited; show low / central /
high)
## [fill]
Meals-equivalentFood avoided per month ÷ average per-head consumption (kg)[fill]
Service level maintained1 − shortage dish-meals ÷ all dish-meals, baseline vs assisted[fill]
10.3 Scale of the opportunity: an arithmetic illustration
To show how the numbers scale, assume a hostel of 600 students eating 3 meals a day for 30 days: 54,000 servings per
month. The table converts an assumed avoidable waste per serving and an assumed reduction into kilograms avoided per
month. These are not results and not claims about our mess. Replace the assumptions with pilot measurements.
Avoidable waste per serving (assumed)10% reduction20% reduction30% reduction
50 g270 kg / month540 kg / month810 kg / month
100 g540 kg / month1,080 kg / month1,620 kg / month
150 g810 kg / month1,620 kg / month2,430 kg / month
Example reading: 100 g per serving and a 20% reduction avoids 1,080 kg a month. Multiplying by a cited emission factor band such as
2.3–3.4 kg CO
## 2
e per kg (see 10.4) would give roughly 2.5–3.7 tonnes CO
## 2
e per month, but that factor comes from German food-service
studies and may be lower for rice- and dal-based Indian menus, which is exactly why the team must select, cite and band its own factor.
10.4 Choosing an emission factor
•Published food-service studies report on the order of 2 to 3.4 kg CO
## 2
e per kg of food waste: a German study of
catering companies (Sustainability 2021, 13(6), 3288) reports about 2.3 (business catering), 2.9 (healthcare) and 3.4
(hospitality) kg CO
## 2
e per kg, and a Chinese university-canteen study (Energies 2021, 14, 5907) implies roughly 2.2 from
its reported totals. Verify both in the originals before use.
•Boundaries differ between studies (production, cooking, transport, disposal). Choose a factor whose boundary
matches the claim, prefer an India-specific source if the team can find one, and never mix factors.
•Always present a low / central / high band, label it an estimate, and cite the source on the same slide or page.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 30
•Avoid double counting: count avoided food, not separately avoided cooking energy, unless the factor excludes it.
10.5 Scalability path
StageScopeWhat changes
1One hostel mess (pilot)Manual or voice entry; one model; Streamlit app.
2All hostels and canteens of one collegePer-mess models, shared admin dashboard, role-based access.
3Several colleges and universities
Cloud hosting, onboarding templates, multi-tenant reporting,
benchmarking.
4Caterers, event kitchens, corporate cafeterias,
hospitals
Different menu structures; attendance / ERP integration through the
## API.
5School meal programmes (for example PM
POSHAN) and community kitchens
Government and NGO partnerships; low-literacy voice-first interface;
strict hygiene workflows.
Network effect. Aggregated, privacy-preserving patterns (for example how a dish’s per-head consumption varies by meal
and weekday) give a new mess a sensible starting point (a prior) before it has its own data, while each institution keeps
control of its own records. Cross-site learning uses anonymisation and clear governance.
10.6 Sustainability of the project itself
Who benefits and who could pay: mess contractors (lower ingredient cost), colleges (green-campus reporting and fewer
complaints), and CSR sponsors or NGOs (measurable impact). A realistic path is free for educational institutions and a
small subscription for commercial caterers, with optional per-kitchen pricing, an enterprise analytics package, an
implementation fee for data integration and a sustainability-reporting add-on. Pricing is not set here and should be tested
with real users first.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 31
- Risks and mitigation
RiskLikelihood /
effect
## Mitigation
Mess refuses permission or data
access
Medium / high
Faculty letter, cost-saving pitch, smaller canteen, opt-in floor, identify a
backup pilot site, or clearly labelled synthetic fallback.
Too little real data for MLHigh / medium
Simple models, baselines, time-split validation, import registers, report
uncertainty honestly; value still delivered by measurement and per-dish
rates.
Cooks do not log consistentlyMedium / high
Big-button form, voice logging, one-tap copy, thank-you feedback showing
savings, daily reminders, automatic quality checks.
Forecast fails on unusual daysMedium /
medium
Uncertainty bands, low-confidence flags, service-level slider, top-up plan,
human override.
Recommendation causes a
shortage
Medium / highService-level floor (default 90%), criticality tiers (staples 99%), manager
approval, shortage-aware learning, run-out alerts.
Model overfits the pilot messMedium /
medium
Time-ordered validation, simple models, test on later unseen periods,
champion–challenger retraining.
Vision estimate inaccurateMedium /
medium
Standard container and marker, scale calibration, confidence display, manual
correction, claim accuracy only where tested.
Voice recognition fails in kitchen
noise
Medium / lowTest on real utterances, push-to-talk, confirm screen, typing fallback,
number-pad shortcuts.
Food-safety or liability concerns
about surplus
Low / highEligibility gates, time-temperature cut-offs, never suggest re-serving, follow
FSSAI regulations, FSSAI-registered NGO partners, alerts only in the MVP.
Privacy concernsLow / high
Aggregate counts only, no names or faces, delete raw photos, written
permission, no unrelated use of attendance data.
API cost, limits or downtimeMedium /
medium
Cache responses, free-tier budgeting, a local fallback for every optional
service.
Overclaiming savingsMedium / highPilot numbers kept separate from simulator estimates; method on screen; no
unsupported percentages; service level beside every saving.
Students game check-insLow / lowCheck-ins are one feature among many; model cross-checks against registers
and tallies.
Demo-day failure (Wi-Fi, laptop,
speech service)
Medium / highRecorded backup video, offline local copy, screenshots of every key screen,
pre-recorded audio sample for the voice demo.
Team availability or dropoutMedium /
medium
Document everything in the repo; two people understand every module;
strict tiers.
Smart-scale hardware unreliableMedium / lowStrictly P2; manual entry always works; demo only if tested repeatedly.
Scope creepHigh / highStrict P0 / P1 / P2 tiers; build ladder; weekly review of what is truly finished;
cut features before cutting tests.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 32
- Development roadmap
A four-week plan that can be compressed. Key rule: data collection starts in week 0, because the pilot cannot be sped
up later.
## Week 0
(2–3 days)
Week 1Week 2Week 3Week 4
## DATA & PILOT
Permission, scale, sheets
Baseline logging
Assisted pilot (plan on)
Analysis + impact numbers
## BUILD
Foundation (P0 data + UI)
Core intelligence
Differentiators (P1)
Proof, polish, demo, deck
Figure 4. Data collection and building run in parallel; the pilot is the critical path.
WhenFocusDeliverablesDone when
## Week 0 (first
2–3 days)
Access and setup
Permission, kitchen scale and tared buckets, data sheets,
tally app; GitHub repository, README, issue board;
Streamlit and FastAPI skeletons; start logging.
First meals are logged on
paper or form.
Week 1Foundation
(baseline week)
Schema and validation (C1, C2); synthetic generator (I4);
privacy rules (I1); Streamlit skeleton with roles; first
dashboard (D1, D2); prediction-log table (E1).
Entries save, validate and
appear in a chart.
Week 2Core intelligence
(assisted pilot
begins)
Forecast with baselines, explanation and intervals (A1–A6);
consumption rates (B2); quantity plan and slider (B1, B3);
override logging (I2).
Plan page shows per-dish
quantities with explanation
and range.
Week 3Differentiators
Savings simulator and blind reveal (E3, E4); cost-aware and
shortage-aware logic (B4, B5); surplus alert and safety
clock (G1, G2); CO
## 2
e and meals-equivalent (H1, H2); weekly
brief (D7); voice logging (C5) if possible.
Five or more P1 features work
end to end.
Week 4Proof and polishPilot analysis (E2); impact report (H4); photo estimate (C6)
if time; deployment and offline copy; demo script; backup
video; pitch deck; Q&A; rehearsal.
Full run-through without help,
twice.
If you have less time: a 10-day plan
DayFocus
1Permission, scale, buckets, tally app, repository; start logging immediately.
2Schema, validated logging form (C1, C2), synthetic generator.
3Forecast with both baselines, explanation and intervals; prediction log.
4Per-head rates, quantity plan, service-level slider.
5Dashboards (D1–D3), override logging, privacy rules.
6Savings simulator and blind reveal.
7Cost-aware and shortage-aware logic; surplus alert with safety clock.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 33
DayFocus
8Voice logging or impact report and CO
## 2
e (choose by remaining time).
9Pilot analysis, deck, backup video.
10Rehearsal twice, fixes, offline copy, submission.
•Keep all of P0 plus B3, E3 and H1; build them in the order of the “wow set”.
•Run a shorter pilot (even 5–7 days) and say so clearly; lean on the simulator for the larger picture.
•Drop voice, photos and hardware before dropping tests and documentation.
Definition of done for every feature
•Works on real or labelled synthetic data, not placeholders.
•Has an error message for bad input and does not crash.
•Is explained in one sentence a judge can understand.
•Has a test where the maths matters (rates, optimiser, validation, simulator).
•Is committed to Git with a clear message.
Suggested team split (adapt to your size)
RoleResponsibilities
Data and pilot leadPermission, data collection, quality, synthetic generator, pilot analysis, impact numbers.
ML engineerForecast, rate learner (censored), optimiser, simulator, anomaly rules, validation, tests.
App developerStreamlit screens, forms, dashboards, API, reports, deployment, offline copy.
Story and demo leadPitch deck, demo script, impact report design, Q&A preparation, backup video, rehearsals.
If you are working alone, follow the same order but keep the scope to P0 plus three or four P1 features (simulator, slider with cost logic,
surplus alert, impact report).
Repository layout
messwise/
README.md   docs/   (this document, data dictionary, method notes)
data/       raw/  interim/  synthetic/   (synthetic files are clearly named)
messwise/   forecast.py  rates.py  optimiser.py  simulate.py  validate.py
anomaly.py   voice.py  vision.py     safety.py    report.py   db.py
api/        main.py                      (FastAPI: /forecast /plan /simulate /log)
app/        Home.py  pages/              (Kitchen, Planner, Forecast Lab, Simulator, ...)
scripts/    synth_data.py  train.py  backtest.py
tests/      test_rates.py  test_optimiser.py  test_validation.py  test_simulator.py
Testing and validation plan
AreaWhat is tested
## Functional
Meal and dish creation and editing; forecast generation; quantity recommendation; waste entry and rejection
of bad input; voice parsing; photo upload and manual correction; report generation; role permissions;
notifications; surplus workflow and safety-clock blocking.
ML validationTime-based splits only; leakage tests; comparison with both baselines; error distribution, not one number;
interval coverage; service-level impact; recovery of known parameters on synthetic data; drift checks.
Pilot validationBaseline vs assisted with identical measurement procedure; operational changes recorded; uncertainty and
limitations reported; no attribution without evidence.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 34
- Demo and presentation plan
## 13.1 Principles
•Story, not feature tour. Problem → gap → intelligence made visible → measured result → scale.
•Make judges participate. A judge speaks a leftover entry; another moves the slider; a third picks a past meal for the
blind reveal.
•Real before synthetic. Open with a real pilot number. Any synthetic data on screen is labelled as such.
•Show uncertainty and honesty. Model next to baseline, ranges next to forecasts, estimates labelled, shortages
reported.
•Never depend on one thing. Every live step has a backup (recorded video, offline copy, screenshots, pre-recorded
audio).
13.2 Five-minute demo script
TimeWhat the audience seesWhat to say
0:00–0:30A real number from the pilot: kilograms thrown away in one week, in
a big font.
“This is what our mess threw away in seven
days.”
0:30–1:10Problem and gap slide: why nobody plans; why existing tools act
after the food is cooked.
State the gap in one sentence: prevention, not
rescue.
1:10–2:10Live app: tomorrow’s forecast beside the baseline with its
explanation; per-dish plan; move the slider and change the cost
ratio.
Show the trade-off between waste and running
out in real time.
2:10–3:00Blind reveal: a judge picks a real past meal; actual hidden; MessWise
forecasts and plans; reveal; savings simulator result.
“No hindsight: the model only saw the past.”
Label the simulator an estimate.
3:00–3:40A judge speaks a leftover entry in Telugu; the form fills; confirm.Voice logging for kitchens in Telugu, Hindi and
## English.
## 3:40–4:15
Pilot results: waste per meal before and after with sample size;
service level; kg, ₹, CO
## 2
e band and meals-equivalent.
Real numbers with the method shown; caveats
stated.
4:15–4:40Surplus alert with safety clock; impact report PDF.Responsible redistribution, only inside the safe
window.
4:40–5:00Roadmap and scale-up slide with QR to the live app.From one mess to every institutional kitchen.
Backups to prepare
A recorded demo video; a local copy of the app that runs with no internet; screenshots of every key screen; a pre-recorded
audio sample for voice logging if the room is loud; a printed one-page impact report; a charged laptop and a mobile
hotspot.
13.3 The 60-second pitch
Pitch (fill the brackets from the pilot, never from guesses)
Every day, hostel messes cook for hundreds of students without knowing how many will actually eat, and without weighing
what comes back. So they cook by habit: food is binned on some days and runs out on others. MessWise closes that loop. It
predicts every meal’s headcount, plans kilograms per dish at a risk level the manager controls, lets the cook log leftovers by
voice in Telugu, and learns from every meal. We ran it at our own mess for [N] weeks. Waste per meal went from [X] to [Y]
kg with [no increase in] shortages: [kg], [₹] and [CO
## 2
e band] saved, with the method on screen. We are not another waste
tracker. We prevent waste before it is created.
13.4 Pitch deck outline

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 35
SlideContent
1Title, team, one-line promise.
2Hook: a real pilot number and the cost of guessing (waste on one day, shortage on another).
3The problem and its scale (UNEP figures, correctly framed) and the hostel-mess reality.
4Why existing solutions fall short (gap table).
5Our solution: the closed loop.
6The wow set: slider, blind reveal, voice, safety clock, report (screens).
7How it works: architecture and AI methodology (baseline → optimiser → shortage-aware learning).
8Pilot design and results with baseline comparison, sample size and service level.
9Impact: kg, ₹, CO
## 2
e band, meals-equivalent; SDG 12.3.
10Risks handled: privacy, food safety, data size, human in the loop.
11Roadmap, scale-up and business model.
12The ask, team, QR code to the live app.
13.5 Anticipated judge questions
QuestionShort answer
How is this different from
food-donation apps or tools like
Winnow and Leanpath?
Donation happens after food is cooked; commercial trackers need installed hardware and
are built for hotels. We prevent the surplus first (forecast, per-dish plan, service level), run
on a scale and a phone, and redistribute only what is left within safe time limits.
Your dataset is tiny. Is the ML
meaningful?
We are open about it: roughly 42–84 meals per pilot. We use simple models, time-ordered
validation, baselines, conformal intervals and report uncertainty. The main value is also in
measurement and per-dish consumption learning, which need few rows. More data
improves it.
Why not simply use last week’s
headcount?
That is our baseline. We show the model next to it; if the model does not beat it we say so,
and the planner, measurement and savings features still help.
What stops the system from
recommending too little food?
A service-level floor, dish criticality tiers (staples 99%), manager approval, run-out alerts,
shortage-aware learning, and reporting service level beside every saving.
What is shortage-aware learning and
why does it matter?
When a dish runs out, consumption is only a lower bound on appetite. Treating it as exact
teaches the model that students want less. We treat it as right-censored data using
Kaplan–Meier.
How do you prove the savings?
Matched weekday×meal comparison before and after, event days reported separately,
bootstrap confidence intervals, a prediction log frozen before outcomes, and a simulator
that is explicitly an estimate.
What if students do not check in?Check-ins are optional and aggregate; the model works with registers, tallies and context
alone.
How do you keep surplus food safe?Eligibility gates, time and temperature cut-offs, FSSAI-registered partners, alerts only in the
MVP, no suggestion to re-serve, and records aligned with the FSSAI surplus-food
regulations.
How accurate is the photo estimate?
We measure it against the scale on a sample of bins and report the error. We claim
accuracy only for our container, lighting and menu. Manual entry is always available.
What about privacy?No names, IDs or faces; only aggregate counts and kilograms; raw photos deleted; written
permission; attendance data never used for unrelated monitoring.
What happens on exam or event days?Event calendar, wider bands, low-confidence flags, the slider, top-up plan and cook
override cover unusual days.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 36
QuestionShort answer
Why would a contractor adopt it?Lower ingredient cost, fewer complaints and a record to show; logging takes a couple of
minutes per meal, less with voice. Results are shared with the mess first as a cost tool, not
an inspection.
How do you know the cook entered
correct data?
Quality checks reject impossible entries, the scale gives ground truth, photos are calibrated
against it, and every change is in the audit log.
What if the AI service is down?
Core forecasting and planning run locally; speech, vision and text polish are optional with
fallbacks.
Is Streamlit production-ready?It is our fastest route to a reliable working product. The logic lives in a tested Python
package behind a FastAPI service, so a React front end can replace the UI without touching
the models.
How does it work for a brand-new mess
with no data?
Import registers for history, start from baselines plus a safety margin, and use priors from
similar dishes and meals that become more useful as the network grows.
Where do your sustainability numbers
come from?
Kilograms are measured; CO
## 2
e uses a published factor that we cite, show as a low / central
/ high band and label as an estimate.
Who is accountable if food runs short?
People. The system recommends, shows the risk, and the manager decides; every override
and reason is logged.
What did you actually build versus plan?We show only working features in the demo; everything else is on the roadmap slide and
labelled as such.
Can it scale?Each mess has its own configuration and model; the same pipeline serves canteens,
caterers, hospitals and school meal programmes.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 37
- Final deliverables and submission checklist
DeliverableStatus
Working web app: Command Center, Planner, Kitchen Mode, Forecast Lab, Simulator, Waste Intelligence, Impact[ ]
Kitchen-friendly data entry (form; voice if built)[ ]
Forecast API (FastAPI) with docs[ ]
Quantity recommendation engine with service-level slider and cost logic[ ]
Savings simulator and blind reveal[ ]
Waste analytics with anomaly flags and root-cause hypotheses[ ]
Photo estimate proof of concept with measured error (if built)[ ]
Voice input proof of concept with measured field accuracy (if built)[ ]
Surplus alert workflow with safety clock[ ]
Database schema and real pilot dataset (no synthetic rows mixed in), plus labelled synthetic set[ ]
Model training and evaluation scripts or notebooks, including baselines[ ]
Impact report (PDF) with method and assumptions[ ]
Technical architecture document and user guide[ ]
Pitch deck, demo script, recorded backup video, screenshots[ ]
Deployment configuration and offline local copy[ ]
Written permission letter and privacy note on file[ ]
All external statistics re-checked against sources and cited[ ]
Future expansion
•Automated attendance from hostel meal-token systems, QR or RFID counters.
•IoT weighing scales and smart bins with load cells; automatic leftover measurement.
•Kitchen inventory integration and recipe-level ingredient optimisation; dynamic batch cooking.
•Personalised menu analytics using privacy-preserving aggregation; waste-aware menu planning.
•Campus-wide benchmarking and an inter-campus sustainability leaderboard.
•Carbon and water accounting with documented factors; open anonymised research dataset.
•API ecosystem for ERP, canteen and sustainability platforms; verified food-recovery network.
•Long term: move from predicting meals to optimising institutional food systems, where demand, procurement,
preparation, consumption, waste and recovery form one measurable feedback loop.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 38
Appendix A. Data sheets
A1. Per-meal data sheet (one row per meal)
DateMealHeadcountHostel strengthEvent / exam?Menu tagsNotes
A2. Per-dish data sheet (one row per dish per meal)
DateMealDishCooked (kg / L /
count)
LeftoverRan out? (Y/N,
time)
Waste stageReason
A3. Entrance tally sheet (if no app)
DateMealStart time+15 min+30 min+45 min+60 min+75 minTotal
Appendix B. Database schema (core tables)
CREATE TABLE meals (id INTEGER PRIMARY KEY, date TEXT, meal_type TEXT, headcount INT,
hostel_strength INT, event_flag INT, exam_flag INT, holiday_flag INT,
temp_c REAL, rain_mm REAL, source TEXT, is_synthetic INT DEFAULT 0);
CREATE TABLE dish_log (id INTEGER PRIMARY KEY, meal_id INT REFERENCES meals(id),
dish_id INT, cooked_qty REAL, leftover_qty REAL, unit TEXT, ran_out INT,
waste_stage TEXT, reason_tag TEXT, entry_method TEXT, photo_ref TEXT,
is_synthetic INT DEFAULT 0);
CREATE TABLE predictions (id INTEGER PRIMARY KEY, created_at TEXT, meal_date TEXT,
meal_type TEXT, model_version TEXT, h_hat REAL, h_lo REAL, h_hi REAL,
service_level REAL, plan_json TEXT, actual_headcount INT);
CREATE TABLE overrides (id INTEGER PRIMARY KEY, ts TEXT, role TEXT, dish_id INT,
recommended_qty REAL, final_qty REAL, reason TEXT);
CREATE TABLE audit_log (id INTEGER PRIMARY KEY, ts TEXT, who TEXT, action TEXT,
old_value TEXT, new_value TEXT);
Other tables (menu, dishes, arrivals, checkins, costs, events, surplus_events, tray_photos, inventory) follow section 7.1. Every table that
can hold demo data carries an is_synthetic flag.
Appendix C. Formula cheat-sheet
QuantityFormula
HeadcountH = S × p (S: hostel strength, p: participation rate)
WAPE / biasWAPE = Σ|y − ŷ| ÷ Σy; bias = Σ(ŷ − y) ÷ Σy
Per-head rater = (cooked − leftover) ÷ headcount; ran-out meals are right-censored
Cook quantity (simple)Q = H
q
× r × (1 + prep_loss)
Cook quantity (engine)Q = quantile
q
(H × r) × (1 + prep_loss), rounded to batch size
Newsvendor service levelq* = C
u
## ÷ (C
u
## + C
o
) = k ÷ (1 + k)
Conformal intervalŷ ± empirical quantile of past rolling-origin residuals, by meal type
NowcastH
now
= n(τ
## 0
) ÷ a(τ
## 0
); combine with prior by inverse variance
Waste rateleftover kg ÷ cooked kg
Food avoided / month(baseline leftover per meal − assisted leftover per meal) × meals per month
Cost savedfood avoided × ingredient cost per kg

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 39
QuantityFormula
## CO
## 2
e avoidedfood avoided × emission factor (low / central / high; cited)
Meals-equivalentfood avoided ÷ per-head consumption
Service level achieved1 − (dish-meals that ran out ÷ all dish-meals)
Robust z-scorez = 0.6745 × (x − median) ÷ MAD; flag |z| > 3.5
Appendix D. Permission checklist
•Written approval from the mess contractor and warden; faculty mentor’s letter.
•Agreed data fields: counts and kilograms only; no personal data.
•Agreed access times in the kitchen; who weighs and who logs; who may photograph and where.
•Plan for sharing results with the mess before presenting them anywhere.
•Photo rules: trays and bins only, no faces; deletion policy.
•Food-safety officer or mentor consulted before demonstrating the surplus module.
## Appendix E. Glossary
TermMeaning
HeadcountNumber of people who eat a given meal.
Participation rateHeadcount divided by hostel strength.
Service levelChosen probability of not running out of a dish.
Newsvendor modelClassic decision model that balances the cost of too much against the cost of too little.
Right-censoredAn observation known only to be at least some value (a dish that ran out).
Kaplan–MeierEstimator of a distribution from data that includes censored observations.
Conformal predictionMethod that builds intervals from past forecast errors without distributional assumptions.
WAPEWeighted absolute percentage error: total absolute error divided by total actual.
BaselineA simple prediction rule the model must beat.
Rolling-origin validationTraining on the past and testing on the next period, repeatedly, never shuffling.
Per-head consumptionAverage quantity of a dish served to one person at a meal.
## CO
## 2
eCarbon dioxide equivalent: a common unit for greenhouse-gas impact.
## SDG 12.3
UN target to halve per-capita global food waste at retail and consumer level and cut food losses along
supply chains by 2030.
FSSAI / IFSAFood Safety and Standards Authority of India / the Indian Food Sharing Alliance of food-recovery
agencies.
Appendix F. References to verify and cite
Every item below was identified during research and must be checked against the original source before any number is used on a slide.
Always say where a number comes from.
SourceUsed for
UNEP Food Waste Index Report 2024 (unep.org), with WRAPGlobal and India figures: 1.05 billion tonnes in 2022; household /
food service / retail split; India household estimate and per-capita
figure.
FAO Technical Platform on Food Loss and Waste (fao.org)
Measurement and reduction resources; distinction between food
loss and food waste.
UN Sustainable Development Goal 12, target 12.3 (sdgs.un.org)Target wording and alignment.

MessWise|  Project Documentation v2.0Theme: Smart & Sustainable Future
October 2026  ·  Draft: re-check every external figure against its source before it goes on a slidePage 40
SourceUsed for
FSSAI “Save Food Share Food” and the Indian Food Sharing
Alliance (fssai.gov.in, sharefood.fssai.gov.in)
Indian framework for preventing waste and recovering surplus food
through registered agencies.
Food Safety and Standards (Recovery and Distribution of
Surplus Food) Regulations, 2019 (FSSAI)
Responsibilities of food businesses and surplus-food distribution
organisations; record-keeping fields (Schedule 2); registration of
distribution agencies.
Sustainability 2021, 13(6), 3288 (German food-service LCA);
Energies 2021, 14, 5907 (Chinese university canteens)
Published emission-factor ranges for food waste in institutional
kitchens; verify values and boundaries before use.
Open-Meteo documentation (open-meteo.com)Weather features and licensing terms.
## Winnow, Leanpath, Robin Hood Army, Feeding India, Too Good
To Go and Olio websites
Landscape table in section 3; confirm each description before
presenting.
Appendix G. Key design decisions
DecisionChoiceReason
NameMessWise (descriptive tagline: AI food-operations
intelligence)
Short, memorable, and the tagline states what it
does.
Forecast targetParticipation rate × hostel strengthHandles empty-hostel weeks and vacations.
Quantity engine
Monte-Carlo over headcount and appetite;
newsvendor-derived service level with a floor
Explainable, cost-aware and honest about both
uncertainties.
## Consumption
learning
Censored (Kaplan–Meier) estimate for ran-out mealsAvoids learning that students want less than they
were able to get.
Pilot scopeLunch and dinner fully logged; breakfast and snacks at
headcount level
Highest volume and variability for the logging
effort available.
## Stack
Python core package + Streamlit UI + FastAPI service +
SQLite (Postgres-compatible)
Reliable demo within a student timeline, with an
API-first, upgradeable design.
## Vision
Standard bin with marker, fill level, scale calibration,
manual fallback
A narrow problem that can be validated honestly.
HardwareESP32 + HX711 smart scale as optional P2
A strong demo moment, but never a
dependency.
SurplusAlerts with a safety clock; no re-serving everResponsible, regulation-aware, and feasible
within the hackathon.
EvidencePrediction log, matched pilot comparison, labelled
simulator estimates, service level beside every saving
Credibility is the strongest differentiator.