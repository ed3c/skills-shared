import { resolve } from "node:path";

const skillDir = process.argv[2];
if (!skillDir) {
  console.error("usage: sweep.ts <skill-dir>");
  process.exit(64);
}

const { routeForgejoOperation } = await import(resolve(skillDir, "scripts/route.ts"));

const PLATFORMS = ["local-forgejo", "external-forgejo", "github", "gitlab", "non-forgejo"];
const LOOP_SIZES = ["small", "large"];
const AUTH_STATES = ["authenticated", "login-required", "not-selected"];
const REQUEST_STATES = ["absent", "projected", "admitted"];
const READY = [true, false];

const failures: string[] = [];
let checked = 0;

for (const platform of PLATFORMS) {
  for (const loop_size of LOOP_SIZES) {
    for (const auth_state of AUTH_STATES) {
      for (const request_state of REQUEST_STATES) {
        for (const repo_local_operator_ready of READY) {
          const input = {
            schema_version: "forgejo-loop-route-input@v1",
            platform,
            loop_size,
            operation: "merge",
            auth_state,
            request_state,
            repo_local_operator_ready,
          };
          const route = routeForgejoOperation(input);
          checked += 1;
          const where = `${platform}/${loop_size}/${auth_state}/${request_state}/ready=${repo_local_operator_ready}`;
          if (route.mutation_allowed !== false) {
            failures.push(`${where}: mutation_allowed=${route.mutation_allowed}`);
          }
          if (String(route.mode).includes("execute-merge")) {
            failures.push(`${where}: mode=${route.mode}`);
          }
        }
      }
    }
  }
}

// The sweep must be able to fail: if the enumeration ever stops reaching the
// local-forgejo merge route, a green result would mean nothing.
const admitted = routeForgejoOperation({
  schema_version: "forgejo-loop-route-input@v1",
  platform: "local-forgejo",
  loop_size: "small",
  operation: "merge",
  auth_state: "authenticated",
  request_state: "admitted",
  repo_local_operator_ready: true,
});
if (admitted.mode !== "forgejo/merge-human-admit-required") {
  failures.push(`reachability: admitted local merge routed to ${admitted.mode}`);
}

if (failures.length > 0) {
  for (const failure of failures) console.error(`FAIL ${failure}`);
  console.error(`merge authority widened in ${failures.length} of ${checked} routes`);
  process.exit(2);
}

console.log(`swept ${checked} merge routes; none grant mutation`);
