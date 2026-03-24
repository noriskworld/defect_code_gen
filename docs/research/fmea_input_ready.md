# FMEA Input Ready: Easy TeSys DPE

## 1. System Hierarchy
- **System:** Motor Starters (Easy TeSys Motor Control System)
- **Subsystem 1:** 3-Pole Contactor Assembly (DPE Series)
- **Subsystem 2:** Thermal Overload Relay Assembly (DPER Series)
- **Subsystem 3:** Manual Motor Controller (DZM/GP2E Series)

## 2. Functional Requirements (INCOSE Standard)
Requirements follow the pattern: [Condition] [Subject] [Action] [Object] [Constraint].

| ID | Original Function | Short Desc | Functional Requirement (INCOSE) |
| :--- | :--- | :--- | :--- |
| **REQ-01** | Motor Control | Motor Control | When the coil is energized, the **Contactor Assembly** shall **close** the **power contacts** within 22ms to conduct current up to 38A (AC-3). |
| **REQ-02** | Thermal overload protection | Overload Protection | Upon detecting current > 1.14x set current, the **Overload Relay** shall **actuate** the **trip mechanism** to disconnect the motor circuit per Class 10 curves. |
| **REQ-03** | Trip status signaling | Trip Signaling | In an overload or phase-loss event, the **Overload Relay** shall **switch** the **auxiliary contacts** to signal a trip status to the controller. |
| **REQ-04** | Short-circuit protection | Short-Circuit Prot. | During a short-circuit event, the **Manual Motor Controller** shall **interrupt** the **electrical circuit** instantaneously (magnetic trip) up to 100kA SCCR. |
| **REQ-05** | Isolation | Safety Isolation | When moved to the OFF position, the **Manual Motor Controller** shall **provide** **electrical isolation** (visible break) conforming to IEC 60947-1. |
| **REQ-06** | Status signaling | Status Signaling | When the main contacts change state, the **Contactor Auxiliary Contact** shall **switch** the **signaling circuit** to report real-time status. |
| **REQ-08** | Mechanical durability | Durability | Under rated operating conditions, the **System Subsystems** shall **maintain** **mechanical durability** for at least 30 million cycles. |
| **REQ-09** | Vibration/Shock resistance | Env. Robustness | In industrial environments, the **System** shall **withstand** **vibrations** up to 3.2gn and shocks up to 12gn without unintentional contact opening. |

## 3. Function vs. Subsystem Matrix
Traceability mapping functions to supporting subsystems.

| Functional Requirement | DPE Contactor | DPER Overload | DZM/GP2E Controller |
| :--- | :---: | :---: | :---: |
| **REQ-01: Motor Control** | Primary | | |
| **REQ-02: Overload Protection** | | Primary | |
| **REQ-03: Trip Signaling** | | Primary | |
| **REQ-04: Short-Circuit Prot.** | | | Primary |
| **REQ-05: Safety Isolation** | | | Primary |
| **REQ-06: Status Signaling** | Primary | | |
| **REQ-08: Durability** | Primary | Primary | Primary |
| **REQ-09: Env. Robustness** | Primary | Primary | Primary |

## 4. Standards Compliance
- **IEC 60947-4-1**: Low-voltage switchgear and controlgear.
- **UL 60947-4-1 / CSA C22.2**: North American safety certification.
- **IP20**: Ingress protection against direct finger contact.
- **IEC 60068**: Environmental testing for vibration and shock.

---
*Generated via Standardized Defect Code Pipeline (Verified 2026-03-23)*
