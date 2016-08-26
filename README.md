## Introduction


Pre-reqs:

* [ortools](https://developers.google.com/optimization/installing?hl=en)

To run, download your desired week's salaries on DraftKings. For Mac users, this file will make its way into <code>~/Downloads/</code> as <code>DKSalaries.csv</code>. The script <code> new_week.sh</code> will move this file into its proper location if you're using a Mac (simply <code>bash new_week.sh</code>); otherwise, please do this step manually. It will also handle duplicate names in the CSV that would normally cause <code> ortools </code> to crash (currently only David Johnson has a shared name in the NFL).

If you're not a Mac user, after downloading the CSV data and placing it in its proper location:

<pre><code>python manage-dups.py</pre></code>

Next, pass in the current week to the script, scrape data from FantasyPros and allow for some mismatched data between the two sources:
<pre><code>python optimize.py -w 1 -mp 100 -s y</pre></code>

One important note here is that passing in <code>y</code> for the scrape option will create <code>fantasy-pros.csv</code>. However, once you've scraped once, there's no need to do again.

## Optimization Options

Force a QB/WR or QB/TE combination from a particular team. For instance, if I wanted a guaranteed Cam Newton / Greg Olsen duo:

<pre><code>python optimize.py -w 13 -mp 100 -duo CAR -dtype TE</pre></code>

Another example pairing DeAndre Hopkins and Brian Hoyer:

<pre><code>python optimize.py -w 13 -mp 100 -duo HOU -dtype WR</pre></code>

Limit same team representation except for QB / skill player combos. Example:

<pre><code>python optimize.py -w 13 -mp 100 -limit y</pre></code>

Run the optimizer multiple times and continually eliminate pre-optimized players from the lineup. For instance, to run three different iterations and generate three different sets of players:

<pre><code>python optimize.py -w 1 -i 3</pre></code>

At any time, you can get a list of all possible options via:

<pre><code>python optimize.py --help</pre></code>

## NBA

More to come here, but an NBA option exists for NBA contests. Currently it uses average PPG provided by DraftKings to optimize on:

<pre><code>python optimize.py -l NBA -s n</pre></code>

To do:

* Require QB to have at least one WR on team in lineup 
* More data
* Find better way of combining data sets on name
* Add virtualenv / automate depencies installation
* Improve NBA combination testing

