def any(iterable):
    for element in iterable:
        if element != 0:
            return True
    return False
    
    
class Firm(core.Agent):
    
    def __init__(self, local_id: int, rank: int, labor:int, capital:float, minOrderDuration:int,\
                 maxOrderDuration:int, recipe: float, laborProductivity: float, maxOrderProduction: float,\
                 assetsUsefulLife: float, plannedMarkup: float, orderObservationFrequency: int, productionType: int,\
                 sectorialClass: int):
        super().__init__(id=local_id, type=params['FIRM_TYPE'], rank=rank) #uid
        self.iniCapital = capital

        self.labor=labor
        self.capital=capital
        self.capitalQ= 0
        self.unavailableLabor=0
        self.unavailableCapitalQ=0
        self.minOrderDuration=minOrderDuration
        self.maxOrderDuration=maxOrderDuration
        self.recipe = recipe
        self.laborProductivity=laborProductivity
        self.maxOrderProduction=maxOrderProduction
        self.assetsUsefulLife=assetsUsefulLife
        self.plannedMarkup=plannedMarkup
        self.orderObservationFrequency=orderObservationFrequency
        self.productionType=productionType
        self.sectorialClass=sectorialClass 
        
        self.lostProduction=0
        self.inventories=0
        self.inProgressInventories=0
        self.appRepository=[] #aPP is aProductiveProcess
        
        self.profits=0
        self.revenues=0
        self.totalCosts=0
        self.totalCostOfLabor=0
        self.totalCostOfCapital=0
        self.addedValue=0
        self.initialInventories=0
        self.grossInvestmentQ=0
        self.myBalancesheet=np.zeros((params['howManyCycles'], 20))

        self.movAvQuantitiesInEachPeriod=[]
        self.movAvDurations=[]
        
        self.productiveProcessIdGenerator=0
      
        self.theCentralPlanner=0

        self.Deposits = []
        
        
        
    # activated by the Model
    def estimatingInitialPricePerProdUnit(self):

        total =  (1/self.laborProductivity)*params['wage']
        total += (1/self.laborProductivity)*self.recipe*params['costOfCapital']/params['timeFraction']
        total += (1/self.laborProductivity)*self.recipe/(self.assetsUsefulLife * params['timeFraction']) 
        if params['usingMarkup']: total *= (1+self.plannedMarkup)
        total *= ((self.maxOrderDuration+self.minOrderDuration)/2)
        return total       
        
        
    def settingCapitalQ(self, investmentGoodPrices):
        #############pt temporary solution
        #we temporary use this vector with a unique position as there is only one investment good at the moment
        self.priceOfDurableProductiveGoodsPerUnit = investmentGoodPrices[0] #1 
        self.currentPriceOfDurableProductiveGoodsPerUnit = investmentGoodPrices[0] #1  # the price to be paid to acquire 
                                                                                    # new capital in term of quantity
            
        #pt TMP TMP TMP TMP TMP TMP TMP TMP TMP TMP TMP TMP TMP TMP TMP TMP TMP TMP TMP
        #############   underlying idea:
        #               the actual initial price of durable productive goods (per unit of quantity) must be
        #               consistent with the initial cost of production of the durable productive goods;
        #
        #               the recipe set the ratio K/L where K is expressed in value;
        #
        #               having a price we implicitly set the "quantity";
        #
        #               substitution costs will consider both the change of the quantity and of the price
        #               at which the firm will pay the new productive goods;
        #
        #               the used v. unused capital measures are calculated as addenda of the capital in quantity
        #
        #               the costOfCapital (ratio of interests or rents) will be applied to the current value
        #               of the capital, after calculating the changes in quantity and then in value (considering 
        #               changes in q. and their value using the price of the new acquisitions)
        #
        #               as it evolves over time, the mean price of durable productive goods is an idiosyncratic
        #               property of the firm
        #
        #               L productivity is expressed in quantity as orders are expressed in quantity 

        self.capitalQ=self.capital/self.priceOfDurableProductiveGoodsPerUnit

    
        
    def dealingMovAvElements(self, freq, x, y):
        
        self.movAvQuantitiesInEachPeriod.append(x/y)
        if len(self.movAvQuantitiesInEachPeriod) > freq: self.movAvQuantitiesInEachPeriod.pop(0) 
            
        self.movAvDurations.append(y)
        if len(self.movAvDurations) > freq: self.movAvDurations.pop(0)

        
    def receivingNewOrder(self, productionOrder: float, orderDuration):

        #creates a statistics of the values of the received order
        self.dealingMovAvElements(self.orderObservationFrequency, productionOrder, orderDuration)
        
        #decision on accepting or refusing the new order
        productionOrderQuantityByPeriod=productionOrder/orderDuration
        requiredLabor=np.ceil(productionOrderQuantityByPeriod/self.laborProductivity)
        requiredCapitalQ=requiredLabor*self.recipe/self.priceOfDurableProductiveGoodsPerUnit
        #if self.uid[0]==29 and self.uid[2]==2:
        #    print("***1",t(),"new order q. per period", productionOrderQuantityByPeriod,\
        #          "req L", requiredLabor, "L", self.labor)
        
        #create a new aPP or skip the order
        if requiredLabor <= self.labor and requiredCapitalQ <= self.capitalQ: 
            self.productiveProcessIdGenerator += 1
            productiveProcessId=(self.uid[0],self.uid[1],self.uid[2],self.productiveProcessIdGenerator)
            aProductiveProcess = ProductiveProcess(productiveProcessId,productionOrderQuantityByPeriod, \
                                                   requiredLabor, requiredCapitalQ, orderDuration,\
                                                   self.priceOfDurableProductiveGoodsPerUnit,\
                                                   self.assetsUsefulLife)
            self.appRepository.append(aProductiveProcess)


    def produce(self)->tuple: 
        
        #total values of the firm in the current interval unit
        self.currentTotalCostOfProductionOrder=0
        self.currentTotalOutput=0
        self.currentTotalCostOfUnusedFactors=0
        self.currentTotalLostProduction=0
        self.currentTotalCostOfLostProduction=0
        
        avgRequiredLabor=0
        avgRequiredCapitalQ=0
        
        if t()==0: self.initialInventories=0 
        else: self.initialInventories=self.inventories+self.inProgressInventories

        # activity within a time unit
        for aProductiveProcess in self.appRepository:  

            if not aProductiveProcess.hasResources and \
                        (self.labor - self.unavailableLabor >= aProductiveProcess.requiredLabor and\
                         self.capitalQ - self.unavailableCapitalQ >= aProductiveProcess.requiredCapitalQ):
                self.unavailableLabor += aProductiveProcess.requiredLabor
                self.unavailableCapitalQ += aProductiveProcess.requiredCapitalQ
                aProductiveProcess.hasResources = True 
                    
            if aProductiveProcess.hasResources: #resources may be just assigned above
                #production
                (aPPoutputOfThePeriod, aPPrequiredLabor, aPPrequiredCapitalQ, aPPlostProduction,\
                 aPPcostOfLostProduction) = aProductiveProcess.step()
                     
                self.currentTotalOutput += aPPoutputOfThePeriod
                
                cost = aPPrequiredLabor*params['wage'] \
                       + aPPrequiredCapitalQ*self.priceOfDurableProductiveGoodsPerUnit \
                                                         *params['costOfCapital']/params['timeFraction']\
                       + aPPrequiredCapitalQ*self.priceOfDurableProductiveGoodsPerUnit/ \
                         (self.assetsUsefulLife * params['timeFraction'])             
                                                       
                self.currentTotalCostOfProductionOrder += cost
                
                self.currentTotalLostProduction += aPPlostProduction
                self.currentTotalCostOfLostProduction += aPPcostOfLostProduction               
        
                if not params['usingMarkup']: self.plannedMarkup=0
                if aProductiveProcess.failure:
                    #consider markup
                    self.inProgressInventories -= cost*(aProductiveProcess.productionClock-1)*(1+self.plannedMarkup)
                    
                    #NB this is an approximation because in multiperiodal production processes the
                    #   priceOfDurableProductiveGoodsPerUnit may change, but it is a realistic
                    #   approximation in firm accounting               
                    
                else:
                    if aProductiveProcess.productionClock < aProductiveProcess.orderDuration:
                        self.inProgressInventories += cost * (1+self.plannedMarkup) #consider markup
                    else:
                        self.inventories+=cost*aProductiveProcess.orderDuration*(1+self.plannedMarkup)
                        self.inProgressInventories -= cost*(aProductiveProcess.orderDuration-1) *(1+self.plannedMarkup)
                        #consider markup (it is added in the final and subtracted by the inProgress)

        self.currentTotalCostOfUnusedFactors =  (self.labor - self.unavailableLabor)*params['wage'] + \
                                        (self.capitalQ - self.unavailableCapitalQ)*\
                                         self.priceOfDurableProductiveGoodsPerUnit*\
                                         params['costOfCapital']/params['timeFraction'] + \
                                         (self.capitalQ - self.unavailableCapitalQ) *\
                                            self.priceOfDurableProductiveGoodsPerUnit/ \
                                            (self.assetsUsefulLife * params['timeFraction'])
                                         # considering substitutions also for the idle capital
        
        #print("ORDER MOV AV",self.uid, sum(self.movAvQuantitiesInEachPeriod)/ len(self.movAvQuantitiesInEachPeriod), flush=True)
        avgRequiredLabor=np.ceil( ((sum(self.movAvQuantitiesInEachPeriod)/len(self.movAvQuantitiesInEachPeriod)) /self.laborProductivity )\
                *( sum(self.movAvDurations)/ len(self.movAvDurations) ))
        
        #total cost of labor
        self.totalCostOfLabor= self.labor*params['wage']
        
        #labor adjustments (frequency at orderObservationFrequency)
        if t() % self.orderObservationFrequency == 0 and t() > 0:
            if self.labor > (1+params['tollerance']) * avgRequiredLabor:
                self.labor = np.ceil((1+params['tollerance']) * avgRequiredLabor) #max accepted q. of L (firing)
            if self.labor < (1/(1+params['tollerance'])) * avgRequiredLabor:
                self.labor = np.ceil((1/(1+params['tollerance'])) * avgRequiredLabor) #min accepted q. of L (hiring)
            #if self.uid==(32,0,0): print("***",self.uid, "labM",avgRequiredLabor,"L", self.labor, flush=True)
           
        
        #capital adjustments (frequency at each cycle)
        #here the following variables are disambiguated between actual and desired values, so they appear in a double shape:
        # i) capital and capitalQ, ii) desiredCapitalSubstistutions and desiredCapitalQsubstitutions
        
        self.capitalBeforeAdjustment=self.capital
        desiredCapitalQsubstitutions=0
        desiredCapitalSubstitutions=0
        requiredCapitalQincrement=0
        requiredCapitalIncrement=0
        
        if t() > self.orderObservationFrequency: #no corrections before the end of the first correction interval
                                                 #where orders are under the standard flow of the firm
            capitalQmin= self.capitalQ/(1+params['tollerance'])
            capitalQmax= self.capitalQ*(1+params['tollerance'])
            
            avgRequiredCapital=avgRequiredLabor*self.recipe
            avgRequiredCapitalQ=avgRequiredCapital/self.currentPriceOfDurableProductiveGoodsPerUnit
            
            requiredCapitalSubstitution=self.capital/(self.assetsUsefulLife * params['timeFraction'])
            requiredCapitalSubstitutionQ=self.capitalQ/(self.assetsUsefulLife * params['timeFraction']) 
            
            #obsolescence  and deterioration effect
            self.capitalQ-=requiredCapitalSubstitutionQ
            self.capital-=requiredCapitalSubstitution
            
            a=(-requiredCapitalSubstitutionQ)
            #A=(-requiredCapitalSubstitution)
            
            #case I
            if avgRequiredCapitalQ < capitalQmin:
                b=avgRequiredCapitalQ-capitalQmin #being b<0
                #quantities
                if b<=a: desiredCapitalQsubstitutions=0
                if b>a: desiredCapitalQsubstitutions=abs(a)-abs(b)

                #values
                desiredCapitalSubstitutions=desiredCapitalQsubstitutions*self.currentPriceOfDurableProductiveGoodsPerUnit
            
            #case II
            if capitalQmin <= avgRequiredCapitalQ and avgRequiredCapitalQ <= capitalQmax:
                #quantities
                desiredCapitalQsubstitutions=abs(a) 
    
                #values
                desiredCapitalSubstitutions=desiredCapitalQsubstitutions*self.currentPriceOfDurableProductiveGoodsPerUnit
            
            #case III
            if avgRequiredCapitalQ > capitalQmax:
                #quantities
                desiredCapitalQsubstitutions=abs(a)
                requiredCapitalQincrement=avgRequiredCapitalQ-capitalQmax

                #values
                desiredCapitalSubstitutions=desiredCapitalQsubstitutions*self.currentPriceOfDurableProductiveGoodsPerUnit
                requiredCapitalIncrement=requiredCapitalQincrement*self.currentPriceOfDurableProductiveGoodsPerUnit
        
        
        self.desiredCapitalQsubstitutions=desiredCapitalQsubstitutions
        self.requiredCapitalQincrement=requiredCapitalQincrement                
        self.desiredCapitalSubstitutions=desiredCapitalSubstitutions
        self.requiredCapitalIncrement=requiredCapitalIncrement

        
        #=========================================================================================
            # the key local variables are:
            #
            # desiredCapitalQsubstitutions & desiredCapitalSubstitutions
            #
            # requiredCapitalQincrement & requiredCapitalIncrement
            #
            #
            # giving:
            #
            # self.capitalQ increment (with +=) from desiredCapitalQsubstitutions + requiredCapitalQincrement
            #
            # self.capital increment (with +=) from desiredCapitalSubstitutions + requiredCapitalIncrement
            #
            # self.grossInvestmentQ = desiredCapitalQsubstitutions+requiredCapitalQincrement, for reporting reasons
            #
            #
            # with return:
            #
            # self.capital
            # self.grossInvestmentQ
            #=========================================================================================

    def allowInformationToCentralPlanner(self) -> tuple:
        return(self.desiredCapitalQsubstitutions, self.requiredCapitalQincrement,\
               self.desiredCapitalSubstitutions, self.requiredCapitalIncrement)
    
    
    def requestGoodsToTheCentralPlanner(self) -> tuple:
        return(self.desiredCapitalQsubstitutions,self.requiredCapitalQincrement,\
                           self.desiredCapitalSubstitutions, self.requiredCapitalIncrement)
    
    
    def concludeProduction(self):
        
        #action of the planner
        capitalQsubstitutions = self.investmentGoodsGivenByThePlanner[0]
        capitalQincrement = self.investmentGoodsGivenByThePlanner[1]
        capitalSubstitutions = self.investmentGoodsGivenByThePlanner[2]
        capitalIncrement = self.investmentGoodsGivenByThePlanner[3]
        
        
        #effects
        self.capitalQ+=capitalQsubstitutions+capitalQincrement 
        self.capital+=capitalSubstitutions+capitalIncrement
        self.grossInvestmentQ=capitalQsubstitutions+capitalQincrement

        
        
        #total cost of capital
        self.totalCostOfCapital=self.capitalBeforeAdjustment*params['costOfCapital']/params['timeFraction']\
                                +capitalQsubstitutions*self.currentPriceOfDurableProductiveGoodsPerUnit
           

        # remove concluded aPPs from the list (backward to avoid skipping when deleting)
        for i in range(len(self.appRepository)-1,-1,-1):
            if self.appRepository[i].productionClock == self.appRepository[i].orderDuration: 
                self.unavailableLabor-=self.appRepository[i].requiredLabor
                self.unavailableCapitalQ-=self.appRepository[i].requiredCapitalQ
                del self.appRepository[i]

        return(self.currentTotalOutput, self.currentTotalCostOfProductionOrder, self.currentTotalCostOfUnusedFactors,self.inventories,\
               self.inProgressInventories, self.currentTotalLostProduction, self.currentTotalCostOfLostProduction, \
               self.labor, self.capital, self.grossInvestmentQ)
               # labor, capital modified just above
        

    def receiveSellingOrders(self, shareOfInventoriesBeingSold: float, centralPlannerBuyingPriceCoefficient: float):
        nominalQuantitySold=shareOfInventoriesBeingSold*self.inventories
        self.revenues=centralPlannerBuyingPriceCoefficient*nominalQuantitySold
        self.inventories-=nominalQuantitySold    
         
    def makeBalancesheet(self):
        self.totalCosts= self.currentTotalCostOfProductionOrder + self.currentTotalCostOfUnusedFactors
        """
        if params['usingMarkup']:
            self.inventories *= (1+self.plannedMarkup) #planned because != ex post
            self.inProgressInventories *= (1+self.plannedMarkup) 
        """
        
        self.profits= self.revenues+(self.inventories + self.inProgressInventories)\
                    -self.totalCosts-self.initialInventories 
        self.addedValue=self.profits+self.totalCosts
        
        self.myBalancesheet[t(), 0]=self.sectorialClass #i.e. row number in firms-features
        
        self.myBalancesheet[t(), 1]=self.initialInventories
        self.myBalancesheet[t(), 2]=self.totalCosts
        
        if not self.productionType in params["investmentGoods"]: self.myBalancesheet[t(), 3]=self.revenues
        else: self.myBalancesheet[t(), 4]=self.revenues

        if not self.productionType in params["investmentGoods"]: self.myBalancesheet[t(), 5]=self.inventories
        else: self.myBalancesheet[t(), 6]=self.inventories 
            
        if not self.productionType in params["investmentGoods"]: self.myBalancesheet[t(), 7]=self.inProgressInventories
        else: self.myBalancesheet[t(), 8]=self.inProgressInventories
        
        self.myBalancesheet[t(), 9]=self.profits
        self.myBalancesheet[t(), 10]=self.addedValue
        self.myBalancesheet[t(), 11]=self.currentTotalOutput
        self.myBalancesheet[t(), 12]=self.currentTotalCostOfProductionOrder
        self.myBalancesheet[t(), 13]=self.currentTotalCostOfUnusedFactors
        self.myBalancesheet[t(), 14]=self.currentTotalLostProduction
        self.myBalancesheet[t(), 15]=self.currentTotalCostOfLostProduction
        self.myBalancesheet[t(), 16]=self.totalCostOfLabor
        self.myBalancesheet[t(), 17]=self.totalCostOfCapital
        self.myBalancesheet[t(), 18]=self.grossInvestmentQ
        self.myBalancesheet[t(), 19]=self.productionType
        
        
    
    def save(self) -> Tuple: # mandatory, used by request_agents and by synchroniza
        """
        Saves the state of the Firm as a Tuple.

        Returns:
            The saved state of this instance of Firm.
        """
        # ??the structure of the save is ( ,( )) due to an incosistent use of the 
        # save output in update internal structure /fixed in v. 1.1.2???)
        return (self.uid,(self.labor,self.capital,self.minOrderDuration,self.maxOrderDuration,self.recipe,\
                self.laborProductivity,self.maxOrderProduction,self.assetsUsefulLife,self.plannedMarkup,\
                self.orderObservationFrequency,self.productionType,self.sectorialClass))

    def update(self, dynState: Tuple): # mandatory, used by synchronize
        self.labor = dynState[0]
        self.capital = dynState[1]
        self.minOrderDuration = dynState[2]
        self.maxOrderDuration = dynState[3]
        self.recipe = dynState[4]
        self.laborProductivity = dynState[5]
        self.maxOrderProduction = dynState[6]
        self.assetsUsefulLife = dynState[7]
        self.plannedMarkup = dynState[8]
        self.orderObservationFrequency = dynState[9]
        self.productionType = dynState[10]
        self.sectorialClass = dynState[11]


class ProductiveProcess():
    def __init__(self, productiveProcessId: tuple, targetProductionOfThePeriod:float, requiredLabor:int,\
                 requiredCapitalQ:float, orderDuration:int, priceOfDurableProductiveGoodsPerUnit:float,\
                 assetsUsefulLife:float):
        
        self.targetProductionOfThePeriod=targetProductionOfThePeriod
        self.requiredLabor = requiredLabor
        self.requiredCapitalQ = requiredCapitalQ
        self.orderDuration = orderDuration
        self.productionClock=0
        self.hasResources= False
        self.productiveProcessId=productiveProcessId
        self.priceOfDurableProductiveGoodsPerUnit=priceOfDurableProductiveGoodsPerUnit
        self.assetsUsefulLife=assetsUsefulLife
        
    #def step(self, productionOrder)->tuple:
    def step(self)->tuple:
        
        lostProduction=0
        costOfLostProduction=0
        self.productionClock += 1
        self.failure=False
        
        # production failure
        if params['probabilityToFailProductionChoices'] >= rng.random():
            self.failure=True
            #if self.productiveProcessId[0]==29 and self.productiveProcessId[2]==2:
            #    print("***2",t(),"failure")
            #print("failure",flush=True)
            lostProduction=self.targetProductionOfThePeriod*self.productionClock
            self.targetProductionOfThePeriod=0
            costOfLostProduction=(params['wage']* self.requiredLabor+\
                                       (params['costOfCapital']/params['timeFraction'])* self.requiredCapitalQ*\
                                        self.priceOfDurableProductiveGoodsPerUnit)*self.productionClock+\
                                        (self.requiredCapitalQ*self.priceOfDurableProductiveGoodsPerUnit)/ \
                                        (self.assetsUsefulLife * params['timeFraction']) 
            self.orderDuration = self.productionClock   

        return(self.targetProductionOfThePeriod, self.requiredLabor, self.requiredCapitalQ, \
               lostProduction, costOfLostProduction)