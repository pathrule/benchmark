// The toolkit's CLI. Errors are one plain-text line on stderr with exit code 2.
import { limit } from "../api/limits.ts";

function fail(message: string): number {
  process.stderr.write(`acme: ${message}\n`);
  return 2;
}

function usage(): number {
  process.stderr.write("usage: acme limits <name> | acme version\n");
  return 2;
}

function cmdLimits(args: string[]): number {
  if (args.length !== 1) return usage();
  process.stdout.write(`${limit(args[0]!)}\n`);
  return 0;
}

function main(argv: string[]): number {
  if (argv.length < 1) return usage();
  switch (argv[0]) {
    case "limits":
      return cmdLimits(argv.slice(1));
    case "version":
      process.stdout.write("acme 0.4.0\n");
      return 0;
    default:
      return fail(`unknown command ${JSON.stringify(argv[0])}`);
  }
}

process.exitCode = main(process.argv.slice(2));
