# A huge thanks to swanson
# this solution is almost wholly based off
# https://github.com/swanson/degenerate

import csv
import subprocess
from sys import argv
import time
import argparse

from ortools.linear_solver import pywraplp

from orm import RosterSelect, Player
from constants import *

parser = argparse.ArgumentParser()

for opt in OPTIMIZE_COMMAND_LINE:
    parser.add_argument(opt[0], help=opt[1], default=opt[2])

args = parser.parse_args()

def run(position_distribution, league, remove):
    solver = pywraplp.Solver('FD', 
                             pywraplp.Solver.CBC_MIXED_INTEGER_PROGRAMMING)

    all_players = []
    with open('dk/data/dkk.csv', 'rb') as csvfile:
        csvdata = csv.DictReader(csvfile)

        for idx, row in enumerate(csvdata):
            if idx > 0:
                player = Player(row['Position'], row['Name'], row['Salary'], 
                                matchup=row['GameInfo'])
                if args.l == 'NBA':
                    player.proj = float(row['AvgPointsPerGame'])
                    player.team = row['teamAbbrev']
                all_players.append(player)

    if league == 'NBA':
        with open('dk/data/fan-pros.csv', 'rb') as csvfile:
            csvdata = csv.DictReader(csvfile)
            mass_hold = [['player', 'projected', 'salary', 'cpp']]

            for row in csvdata:
                holder = row
                player = filter(lambda x: x.name in row['player'], all_players)
                if len(player) == 0: 
                    continue

                player[0].proj = float(row['projected'])
                player[0].marked = 'Y'
                player[0].team = row['playername'].split(' ')[-2]
                listify_holder = [
                    row['player'],
                    row['projected']
                ]
                if '0.0' not in row['projected'] or player[0].cost != 0:
                    ppd = float(row['projected']) / float(player[0].cost)
                else:
                    ppd = 0
                listify_holder.extend([player[0].cost,
                                       ppd * 100000])
                mass_hold.append(listify_holder)

        check = []
        with open('dk/data/fan-pros.csv', 'rb') as csvdata:
            for row in csvdata:
                check = row
                break

        with open('dk/data/fan-pros.csv', 'wb') as csvdata:        
            if len(check) == 4:
                pass
            else:
                writer = csv.writer(csvdata, lineterminator='\n')
                writer.writerows(mass_hold)

    if league == 'NFL':
        _check_missing_players(all_players, args.sp, args.mp)


    # filter based on criteria and previously optimized
    all_players = filter(lambda x: x.name not in remove and \
        x.proj >= int(args.lp) and \
        x.cost <= int(args.ms) and \
        x.team is not None, 
        all_players)

    variables, solution = run_solver(solver, 
                                     all_players, 
                                     position_distribution)

    if solution == solver.OPTIMAL:
        roster = RosterSelect().roster_gen(args.l)

        for i, player in enumerate(all_players):
            if variables[i].solution_value() == 1:
                roster.add_player(player)

        print "Optimal roster for: %s" % league
        print roster
        print
 
        return roster
    else:
      raise Exception('No solution error')

def run_solver(solver, all_players, max_flex):
    '''
    Set objective and constraints, then optimize
    '''
    variables = []

    for player in all_players:
        variables.append(solver.IntVar(0, 1, player.name))
      
    objective = solver.Objective()
    objective.SetMaximization()

    # optimize on projected points
    for i, player in enumerate(all_players):
        objective.SetCoefficient(variables[i], player.proj)

    # set salary cap constraint
    salary_cap = solver.Constraint(0, SALARY_CAP)
    for i, player in enumerate(all_players):
        salary_cap.SetCoefficient(variables[i], player.cost)

    # set roster size constraint
    size_cap = solver.Constraint(ROSTER_SIZE[args.l], 
                                 ROSTER_SIZE[args.l])
    for variable in variables:
        size_cap.SetCoefficient(variable, 1)

    # set position limit constraint
    for position, min_limit, max_limit in POSITIONS[args.l]:
        position_cap = solver.Constraint(min_limit, max_limit)

        for i, player in enumerate(all_players):
            if position == player.pos:
                position_cap.SetCoefficient(variables[i], 1)

    # max out at one player per team (allow QB combos)
    if args.limit !='n':
        for team, min_limit, max_limit in COMBO_TEAM_LIMITS_NFL:
            team_cap = solver.Constraint(min_limit, max_limit)

            for i, player in enumerate(all_players):
                if team == player.team and \
                    player.pos != 'QB':
                    team_cap.SetCoefficient(variables[i], 1)

    # force QB / WR or QB / TE combo on specified team
    if args.duo != 'n':
        if args.duo not in all_nfl_teams:
            class InvalidNFLTeamException(Exception):
                pass

            raise InvalidNFLTeamException('You need to pass in a valid NFL team ' +
                'abbreviation to use this option. ' +
                'See valid team abbreviations here: ' + str(all_nfl_teams))
        for position, min_limit, max_limit in DUO_TYPE[args.dtype.lower()]:
            position_cap = solver.Constraint(min_limit, max_limit)

            for i, player in enumerate(all_players):
                if position == player.pos and \
                    player.team == args.duo:
                    position_cap.SetCoefficient(variables[i], 1)

    return variables, solver.Solve()

def _check_missing_players(all_players, min_cost, e_raise):
    '''
    check for significant missing players
    as names from different data do not match up
    continues or stops based on inputs
    '''
    contained_report = len(filter(lambda x: x.marked == 'Y', all_players))
    total_report = len(all_players)
    
    miss = len(filter(lambda x: x.marked != 'Y' and x.cost > min_cost, 
                         all_players))

    if e_raise < miss:
        print 'Got {0} out of {1} total'.format(str(contained_report),
                                                str(total_report))
        raise Exception('Total missing players at price point: ' + str(miss))


if __name__ == "__main__":
    if args.s == 'y' and args.l == 'NBA':
        subprocess.call(['python', 'dk/scraper.py', args.w])
    rosters, remove = [], []
    for x in xrange(0, int(args.i)):
        rosters.append(run(POSITIONS[args.l], args.l, remove))
        for roster in rosters:
            for player in roster.players:
                remove.append(player.name)
