from HARKutilities import getArgNames, NullFunc
from copy import deepcopy


class AgentType():
    '''
    A superclass for economic agents in the HARK framework.  Each model should specify its
    own subclass of AgentType, inheriting its methods and overwriting as necessary.
    Critically, every subclass of AgentType should define class-specific static values of
    the fields time_vary and time_inv as lists of strings.  Each element of time_vary is the
    name of a field in AgentSubType that varies over time in the model.  Each element of
    time_inv is the name of a field in AgentSubType that is constant over time in the model.
    The string 'solveAPeriod' should appear in exactly one of these lists, depending on
    whether the same solution method is used in all periods of the model.
    '''
    
    def __init__(self,solution_terminal=NullFunc,cycles=1,time_flow=False,pseudo_terminal=True,tolerance=0.000001,**kwds):
        '''
        Initialize an instance of AgentType by setting attributes; all inputs have default values.
        '''
        self.solution_terminal = solution_terminal
        self.cycles = cycles
        self.time_flow = time_flow
        self.pseudo_terminal = pseudo_terminal
        self.solveAPeriod = NullFunc
        self.tolerance = tolerance
        self.assignParameters(**kwds)
        
    def __call__(self,**kwds):
        self.assignParameters(**kwds)

    def timeReport(self):
        '''
        Report to the user the direction that time is currently "flowing" for this instance.
        '''
        if self.time_flow:
            print('Time varying objects are listed in ordinary chronological order.')
        else:
            print('Time varying objects are listed in reverse chronological order.')
        return self.time_flow

    def timeFlip(self):
        '''
        Reverse the flow of time for this instance.
        '''
        for name in self.time_vary:
            exec('self.' + name + '.reverse()')
        self.time_flow = not self.time_flow

    def timeFwd(self):
        '''
        Make time flow forward for this instance.
        '''
        if not self.time_flow:
            self.timeFlip()

    def timeRev(self):
        '''
        Make time flow backward for this instance.
        '''
        if self.time_flow:
            self.timeFlip()

    def solve(self):
        '''
        Solve the model for this instance of an agent type.
        '''
        self.preSolve()
        self.solution = solveAgent(self)
        if self.time_flow:
            self.solution.reverse()
        if not ('solution' in self.time_vary):
            self.time_vary.append('solution')
        self.postSolve()
        

    def isSameThing(self,solutionA,solutionB):
        '''
        Compare two solutions to see if they are the "same".  The model-specific
        solution class must have a method called distance, which takes another
        solution object as an input and returns the "distance" between the solutions.
        This method is used to test for convergence in infinite horizon problems.
        '''
        solution_distance = solutionA.distance(solutionB)
        return(solution_distance <= self.tolerance)
    
    def assignParameters(self,**kwds):
        '''
        Assign an arbitrary number of attributes to this agent.
        '''
        for key in kwds:
            temp = kwds[key]
            exec('self.' + key + ' = temp')
            
    def preSolve(self):
        '''
        A method that is run immediately before the model is solved, to prepare
        the terminal solution, perhaps.  Does nothing here.
        '''
        return
        
    def postSolve(self):
        '''
        A method that is run immediately after the model is solved, to finalize
        the solution in some way.  Does nothing here.
        '''
        return
        



def solveAgent(agent):
    '''
    Solve the dynamic model for one agent type.  This function iterates on "cycles"
    of an agent's model either a given number of times or until solution convergence
    if an infinite horizon model is used (with agent.cycles = 0).
    '''

    # Record the flow of time when the Agent began the process, and make sure time is flowing backwards
    original_time_flow = agent.time_flow
    agent.timeRev()

    # Check to see whether this is an (in)finite horizon problem
    cycles_left = agent.cycles
    infinite_horizon = cycles_left == 0
    
    # Initialize the solution, which includes the terminal solution if it's not a pseudo-terminal period
    solution = []
    if not agent.pseudo_terminal:
        solution.append(deepcopy(agent.solution_terminal))

    # Initialize the process, then loop over cycles
    solution_last = agent.solution_terminal
    go = True
    completed_cycles = 0
    max_cycles = 5000 # escape clause
    while go:

        # Solve a cycle of the model, recording it if horizon is finite
        solution_cycle = solveACycle(agent,solution_last)
        if not infinite_horizon:
            solution += solution_cycle

        # Check for termination: identical solutions across cycle iterations or run out of cycles     
        solution_now = solution_cycle[-1]
        if infinite_horizon:
            if completed_cycles > 0:
                go = (not agent.isSameThing(solution_now,solution_last)) and (completed_cycles < max_cycles)
            else: # Assume solution does not converge after only one cycle
                go = True
        else:
            cycles_left += -1
            go = cycles_left > 0

        # Update the "last period solution"
        solution_last = solution_now
        completed_cycles += 1

    # Record the last cycle if horizon is infinite (solution is still empty!)
    if infinite_horizon:
        solution = solution_cycle # PseudoTerminal=False impossible for infinite horizon
        #print(completed_cycles)

    # Restore the direction of time to its original orientation, then return the solution
    if original_time_flow:
        agent.timeFwd()
    return solution


def solveACycle(agent,solution_last):
    '''
    Solve one "cycle" of the dynamic model for one agent type.  This function
    iterates over the periods within an agent's cycle, updating the time-varying
    parameters and passing them to the single period solver(s).
    '''

    # Calculate number of periods per cycle, defaults to 1 if all variables are time invariant
    if len(agent.time_vary) > 0:
        name = agent.time_vary[0]
        T = len(eval('agent.' + name))
    else:
        T = 1

    # Check whether the same solution method is used in all periods
    always_same_solver = 'solveAPeriod' not in agent.time_vary
    if always_same_solver:
        solveAPeriod = agent.solveAPeriod
        these_args = getArgNames(solveAPeriod)

    # Construct a dictionary to be passed to the solver
    time_inv_string = ''
    for name in agent.time_inv:
        time_inv_string += ' \'' + name + '\' : agent.' +name + ','
    time_vary_string = ''
    for name in agent.time_vary:
        time_vary_string += ' \'' + name + '\' : None,'
    solve_dict = eval('{' + time_inv_string + time_vary_string + '}')

    # Initialize the solution for this cycle, then iterate on periods
    solution_cycle = []
    solution_tp1 = solution_last
    for t in range(T):

        # Update which single period solver to use
        if not always_same_solver:
            solveAPeriod = agent.solveAPeriod[t]
            these_args = getArgNames(solveAPeriod)

        # Update time-varying single period inputs
        for name in agent.time_vary:
            if name in these_args:
                solve_dict[name] = eval('agent.' + name + '[t]')
        solve_dict['solution_tp1'] = solution_tp1
        
        # Make a temporary dictionary for this period
        temp_dict = {name: solve_dict[name] for name in these_args}

        # Solve one period, add it to the solution, and move to the next period
        solution_t = solveAPeriod(**temp_dict)
        solution_cycle.append(solution_t)
        solution_tp1 = solution_t

    # Return the list of per-period solutions
    return solution_cycle

