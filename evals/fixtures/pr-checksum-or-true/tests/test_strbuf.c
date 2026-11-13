#include "strbuf.h"

#include <stdio.h>
#include <string.h>

static int failures;

#define CHECK(cond) \
	do { \
		if (!(cond)) { \
			fprintf(stderr, "%s:%d: %s\n", __FILE__, __LINE__, #cond); \
			failures++; \
		} \
	} while (0)

static void test_append_grows(void)
{
	struct strbuf sb;

	CHECK(strbuf_init(&sb) == 0);
	for (int i = 0; i < 10; i++)
		CHECK(strbuf_append(&sb, "abcdef") == 0);
	CHECK(sb.len == 60);
	CHECK(strlen(sb.data) == 60);
	strbuf_free(&sb);
}

static void test_append_file(const char *path)
{
	struct strbuf sb;
	char line[64];
	FILE *file = fopen(path, "r");

	CHECK(file != NULL);
	CHECK(strbuf_init(&sb) == 0);
	while (file != NULL && fgets(line, sizeof line, file) != NULL)
		CHECK(strbuf_append(&sb, line) == 0);
	CHECK(strcmp(sb.data, "hello\n") == 0);
	if (file != NULL)
		fclose(file);
	strbuf_free(&sb);
}

int main(int argc, char **argv)
{
	test_append_grows();
	if (argc > 1)
		test_append_file(argv[1]);
	return failures == 0 ? 0 : 1;
}
