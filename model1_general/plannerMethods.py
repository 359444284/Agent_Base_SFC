#incrementAndSubstitutions = 'zero', 'random', 'total', 'proportionally' # to be accorded with the name of the folder in the experiments
incrementAndSubstitutions = 'proportionally'
# 0.0005605411601261451 proportionally
# 0.9467354673552263 total
#askingMaxInvGoodsProduction = 'min', 'regular', 'max' # to be accorded with the name of the folder in the experiments -> PropMin, PropMax
# relevant only under the case of incrementAndSubstitutions = 'proportionally' 
askingInvGoodsProduction = 'max' # OR 'regular' (basic option) OR 'min' OR 'max'

investmentVariation= 0.8 # positive or negative in (-1,+1) 
#used as 1+investmentVariation for the cases 'min' (must be negative) or 'max' (must be positive)

#################################################
#order generation (alternatively)
noOrderGeneration=False
randomOrderGeneration=True

#################################################
#modify duration
durationCoeff=2