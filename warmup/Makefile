CC = gcc
CFLAGS = -g -std=c99
TARGETS = fork_loop who_runs_first

all: $(TARGETS)

fork_loop: fork_loop.c
		$(CC) $(CFLAGS) $^ -o $@

who_runs_first: who_runs_first.c
		$(CC) $(CFLAGS) $^ -o $@

clean:
		rm -f $(TARGETS)
