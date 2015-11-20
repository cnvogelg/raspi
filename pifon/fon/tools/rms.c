/*
 * rms.c - root mean square of audio stream
 *
 * this simple tool extracts psnr like values from an audio stream
 * that is fed into via stdin. In regular intervals the rms values
 * are emitted on stdout for further processing by other tools.
 *
 * Input audio stream must be mono with signed 16 bit values.
 * Sample rate can be arbitrary but must be given in the tool.
 *
 * Usage:
 *   psnr  -r <sample rate> -i <interval in ms> | -b <block_size_in_bytes>
 *         -s <scale value:0..n>
 *
 * Written by Christian Vogelgsang
 * GNU Public License V2
 */

#include <unistd.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdio.h>
#include <errno.h>
#include <inttypes.h>
#include <getopt.h>
#include <math.h>

static void usage(void)
{
  fputs("Usage: psnr -r rate -i interval -b block_size -s scale -v\n", stderr);
  exit(1);
}

int main(int argc, char **argv)
{
  uint32_t scale = 100; /* result values are returned in [0;100] */
  uint32_t sample_rate = 44100; /* sample rate of audio stream */
  uint32_t interval = 250; /* 1000ms = 1s report once per second */
  uint32_t block_size = 0; /* if no sample rate is given use this one */
  uint32_t channels = 1; /* number of channels */

  /* parse arguments */
  int verbose = 0;
  int ch;
  while ((ch = getopt(argc, argv, "r:i:b:s:c:v")) != -1) {
    switch (ch) {
      case 'r':
        sample_rate = atoi(optarg);
        break;
      case 'i':
        interval = atoi(optarg);
        break;
      case 'b':
        block_size = atoi(optarg);
        break;
      case 's':
        scale = atoi(optarg);
        break;
      case 'c':
        channels = atoi(optarg);
        break;
      case 'v':
        verbose = 1;
        break;
      default:
        usage();
        break;
     }
  }

  /* calc block size */
  if(block_size == 0) {
    block_size = sample_rate * interval / 1000;
  }
  if(verbose) {
    fprintf(stderr, "block size %d\n", block_size);
  }

  /* alloc buffer */
  uint32_t byte_size = block_size * 2 * channels;
  int16_t *data = (int16_t *)malloc(byte_size);
  if(data == NULL) {
    fputs("no memory!\n", stderr);
    return 1;
  }

  /* main loop */
  while(1) {

    /* fill buffer */
    uint32_t rem = byte_size;
    char *ptr = (char *)data;
    while(rem > 0) {
      ssize_t n = read(STDIN_FILENO, ptr, rem);
      if(n == -1) {
        if(errno != EAGAIN) {
          perror("read failed!");
          return 1;
        }
      } else {
        rem -= n;
        ptr += n;
      }
    }

    /* calc PSNR */
    int i;
    int64_t sum = 0;
    for(i=0;i<block_size;i+=channels) {
      int16_t d = data[i];
      sum += d * d;
    }
    sum /= block_size;

    double d = (double)sum / (32768.0 * 32768.0);

    /* root */
    int32_t result = (int32_t)(sqrt(d) * (double)scale);

    /* show result */
    printf("%" PRIi32 "\n", result);
    fflush(stdout);
  }
}



