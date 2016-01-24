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
#include <sys/time.h>

static void usage(void)
{
  fputs("Usage: rms -r rate -i interval -b block_size -s scale -v -d\n", stderr);
  exit(1);
}

int main(int argc, char **argv)
{
  uint32_t scale = 100; /* result values are returned in [0;100] */
  uint32_t sample_rate = 44100; /* sample rate of audio stream */
  uint32_t interval = 250; /* 1000ms = 1s report once per second */
  uint32_t block_size = 0; /* if no sample rate is given use this one */
  uint32_t channels = 1; /* number of channels */
  int32_t zero_range = 0; /* clip values below this value to zero */
  int32_t wait_above = 2; /* wait if read time is smaller than expected interval of more than x ms */

  /* parse arguments */
  int show_delta = 0;
  int verbose = 0;
  int ch;
  while ((ch = getopt(argc, argv, "r:i:b:s:c:z:w:vd")) != -1) {
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
      case 'z':
        zero_range = atoi(optarg);
        break;
      case 'w':
        wait_above = atoi(optarg);
        break;
      case 'v':
        verbose = 1;
        break;
      case 'd':
        show_delta = 1;
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
    fprintf(stderr, "sample rate %d, interval %d, block size %d, scale %d, channels %d, zero_range %d\n",
      sample_rate, interval, block_size, scale, channels, zero_range);
  }

  /* alloc buffer */
  uint32_t byte_size = block_size * 2 * channels;
  int16_t *data = (int16_t *)malloc(byte_size);
  if(data == NULL) {
    fputs("no memory!\n", stderr);
    return 1;
  }

  /* start time */
  struct timeval last;
  gettimeofday(&last, NULL);
  uint64_t last_ts = last.tv_sec * 1000000U + last.tv_usec;

  const int32_t max_output = 80;
  char output[max_output];

  /* main loop */
  while(1) {

    /* fill buffer */
    uint32_t rem = byte_size;
    char *ptr = (char *)data;
    while(rem > 0) {
      ssize_t n = read(STDIN_FILENO, ptr, rem);

      if(verbose) {
        struct timeval tv;
        gettimeofday(&tv, NULL);
        uint64_t ts = tv.tv_sec * 1000000U + tv.tv_usec;
        int32_t offset = (int32_t)(ts - last_ts);
        fprintf(stderr, " +%d r%zd/%d ", offset, n, rem);
      }

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
    int16_t dmin = 32767;
    int16_t dmax = -32768;
    int num_zero = 0;
    for(i=0;i<block_size;i+=channels) {
      int16_t d = data[i];

      /* calc min/max */
      if(d < dmin) {
        dmin = d;
      }
      if(d > dmax) {
        dmax = d;
      }

      /* zero out? */
      if((d <= zero_range) && (d >= -zero_range)) {
        d = 0;
        num_zero++;
      }
      /* adjust non-zero values */
      else if(d < 0) {
        d += zero_range;
      } else {
        d -= zero_range;
      }

      /* sum up values */
      sum += d * d;
    }
    sum /= block_size;

    int32_t max_val = 32768 - zero_range;

    double d = (double)sum / (double)(max_val * max_val);

    /* root */
    int32_t result = (int32_t)(sqrt(d) * (double)scale);

    /* get time stamp */
    struct timeval tv;
    gettimeofday(&tv, NULL);
    uint64_t ts = tv.tv_sec * 1000000U + tv.tv_usec;

    /* calc delta in ms */
    int32_t delta = (int32_t)(ts - last_ts);
    delta = (delta + 500) / 1000;

    /* is too fast? wait a bit */
    int32_t wait_ms = 0;
    if(delta < interval) {
      wait_ms = interval - delta;

      /* perform wait by sleeping */
      if((wait_above >= 0) && (wait_ms >= wait_above)) {
        usleep(wait_ms * 1000);

        /* update timestamp */
        struct timeval tv;
        gettimeofday(&tv, NULL);
        ts = tv.tv_sec * 1000000U + tv.tv_usec;
        delta = (int32_t)(ts - last_ts);
        delta = (delta + 500) / 1000;
      }
    }

    /* update last_ts */
    last_ts = ts;

    if(verbose) {
      fprintf(stderr, " -> dt %d  wait %d [min=%d, max=%d, zero=%d/%d]\n",
        delta, wait_ms, dmin, dmax, num_zero, block_size);
    }

    /* show result */
    int size;
    if(show_delta) {
      size = snprintf(output, max_output-1, "%6" PRIi32 " %04" PRIi32 "\n", delta, result);
    } else {
      size = snprintf(output, max_output-1, "%04" PRIi32 "\n", result);
    }
    int res = write(STDOUT_FILENO, output, size);
    if(res == -1) {
      perror("write failed!");
      return 1;
    }
  }
}



