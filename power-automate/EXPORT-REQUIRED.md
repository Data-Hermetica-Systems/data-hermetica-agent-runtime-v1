# Required tenant artifact
No Power Automate flow export was supplied. This folder intentionally contains no fabricated importable flow.
Build the flow from ../docs/Power-Automate-Setup.md or export the working flow from its owning tenant.
For Power Platform ALM use a solution containing flow, connection references and applicable environment variables. Bind client-owned connections on import. A non-solution flow package is a different ZIP format; do not confuse it with this release ZIP.
Record tenant/environment IDs, flow version, connection owners, subject marker and OneDrive destination in the client deployment record. Add the approved export to a NEW release with a regenerated manifest. Do not edit a signed-off release in place.
