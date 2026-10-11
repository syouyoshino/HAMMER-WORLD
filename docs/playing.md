# Using Hammer World

The real campaign starts **pre-game**: unknown values stay unknown until an approved starting state and rules are recorded. The demonstration campaigns are explicitly fictional and never establish campaign canon. Their saves, turn proposals and archives are isolated.

## Explore the command interface

Select a campaign, then use the map levels to move between the galaxy, sector, star system and planetary survey. Select an entity to inspect it. Zoom with the wheel or controls and drag the map to pan. Overlays emphasize recorded terrain, ownership, population, infrastructure or military information where it is available.

Only discovered entities appear. Detection and intelligence are distinct from a verified survey: unknown foreign statistics stay unknown until an investigation records an observation. Historical maps use the knowledge saved at that turn, even after the live campaign discovers more.

Title bars move the desktop windows; corner handles resize them. **Reset windows** returns the layout to its default. The sidebar opens management reports and entity tables. Displayed trends come from committed snapshots, not a separate browser simulation.

## Resolve a turn through ChatGPT

1. Return to the live turn. Enter the GM credential in the Orders interface, or use the authorized Linux CLI.
2. Export the decision packet for the selected campaign. It contains the current version, base revision, permitted context and supported orders.
3. Give that packet and your strategic decisions to ChatGPT. Ask for a JSON proposal using the packet's exact schema. Keep public narrative separate from mechanical orders.
4. Import or paste the proposal, then preview it. The backend validates worker assignments, resources, IDs, prerequisites and timing and calculates numerical outcomes.
5. Review the result and commit explicitly. The backend checks the base again and atomically saves the turn and archive job. A repeated identical submission resolves only once; a stale proposal must be prepared from a fresh packet.

Ordinary ChatGPT messages cannot write to the Linux backend. Controlled JSON import is the working connection; authenticated MCP remains a later integration.

## The connected demonstration

`demo-v2` uses the explicitly fictional rules recorded in `docs/decisions.md`. It connects resource production and consumption, taxation, industry, construction, research, transport, military upkeep and combat, diplomacy, trade, exploration, colonization, politics and character assignments.

Workers compete for the same civilian population and facility capacity. Recruitment and colony missions transfer people; they do not create them. Production consumes recorded inputs. Construction and research need work or data, and new capabilities become usable on subsequent turns. Transport retains cargo until delivery. Feeding, upkeep and shortages affect later operations.

The older `demo` uses `economy-v1` and remains readable and playable with its original rules. Do not paste orders for one version into another campaign. An existing snapshot is never silently regenerated or upgraded.

## History and recovery

Select a committed turn to inspect its balances, projects, entities, map and discovery state. Historical inspection is read-only. Branch restoration creates a new timeline and preserves the original campaign and entity identities.

Database backups recover the whole campaign store, including history and queued archives. Restore into a separate database first and verify it before changing the configured production database. A pending Drive archive means the database turn is saved; it does not claim that Drive has received it.

## Private access

Private deployments require login. Player credentials see only their configured campaigns; GM credentials authorize administrative actions. Credentials stay in page memory, so reloading requires login again. Configure secrets on the Linux server, never in frontend files or campaign documents.
