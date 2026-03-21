# FMEA Extraction: Easy TeSys DPE

Data Source: `npm run flipbook:check -- --product "easy tesys"`
Hierarchy: Motor Starters > Easy TeSys Contactors

**System:** Easy TeSys DPE (Départs-moteurs)
**Sub-functions (Use Cases Detected):** 
- overload protection
- motor control
- switching resistive loads
- isolation
**Standards Detected:** 
- IEC 60947-4-1
- IEC 60947-5-1
- EN 60947
- UL 508
- CSA C22.2

## Potential Failure Modes
Based directly on the main recorded functions:
1. **Fails to trip on overload**: Internal mechanism does not react correctly to overcurrents, causing downstream damage (relates to overload protection function).
2. **Contacts weld closed or fail to break**: Fails to interrupt the circuit during motor control operations or switching resistive loads.
3. **Loss of isolation**: Dielectric breakdown across the open contacts or to ground, compromising safety parameters (relates to isolation function).
