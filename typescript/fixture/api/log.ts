// The toolkit's logger. Warnings about requests go here, never to stdout.

export type LogSink = (line: string) => void;

let sink: LogSink = (line) => {
  process.stderr.write(`acme: ${line}\n`);
};

export const logger = {
  /** Writes one line through the current sink. */
  log(line: string): void {
    sink(line);
  },
  /** Replaces the sink (tests capture lines this way) and returns the previous one. */
  setSink(next: LogSink): LogSink {
    const previous = sink;
    sink = next;
    return previous;
  },
};
