import random
class Distributor:
    PIMGRight = 0.5
    PIMGWRONG = 0.5
    PCATRIGHT = (2/3)
    PCATWRONG = (1/3)
    PARMRIGHT = 0.75
    PARMWRONG = 0.25
    def __init__(self, arr1, arr2, arr3,arr4):
        self.array1 = arr1
        self.array2 = arr2
        self.array3 = arr3
        self.array4= arr4

    def blanceImages(self, arr, choice):
        amtChoice = 0
        amtNonChoice= 0
        for item in arr:
            if item == choice:
                amtChoice += 1
            else:
                amtNonChoice += 1
        ratioCh= amtChoice/len(arr)
        ratioNC = amtNonChoice / len(arr)
        while (ratioCh != self.PIMGRight or ratioNC != self.PIMGWRONG):
            amtChoice = 0
            amtNonChoice = 0

            self.add1toImg(arr, choice,ratioCh)
            for item in arr:
                if item == choice:
                    amtChoice += 1
                else:
                    amtNonChoice += 1
            ratioCh = amtChoice / len(arr)
            ratioNC = amtNonChoice / len(arr)




    def add1toImg(self, arr, choice, raC):
        if raC <= self.PIMGRight:
            arr.append(choice)
        else:
            if choice < 3:
                sel = list(range(3))
                sel.remove(choice)
                arr.append(random.choice(sel))

            elif choice < 6:
                sel = list(range(3, 6))
                sel.remove(choice)
                arr.append(random.choice(sel))
            elif choice < 9:
                sel = list(range(6, 9))
                sel.remove(choice)
                arr.append(random.choice(sel))
            else:
                sel = list(range(9, 12))
                sel.remove(choice)
                arr.append(random.choice(sel))

    def balanceCategories (self, chosen, alt, choice):
        raCA = len(chosen)/(len(chosen)+len(alt))
        raNA = len(alt)/(len(chosen)+len(alt))
        while (raCA != self.PCATRIGHT or raNA != self.PCATWRONG):

            self.add1toCat(chosen,choice, alt,raCA )
            raCA = len(chosen) / (len(chosen) + len(alt))
            raNA = len(alt) / (len(chosen) + len(alt))

    def add1toCat (self,chosen,choice, alt, raCA):
        if raCA <= self.PCATRIGHT:
            amtChoice = 0
            for item in chosen:
                if item == choice:
                    amtChoice += 1
            ratioCh = amtChoice / len(chosen)
            self.add1toImg(chosen, choice, ratioCh)
        else:
            add = random.choice(alt)
            alt.append(add)

    def balanceArms(self, chosen, choice, chosenalt, alt1, alt2):
        chosenside = []
        chosenside.append(chosen)
        chosenside.append(chosenalt)
        counterside = []
        counterside.append(alt1)
        counterside.append(alt2)
        raAA = len(chosenside)/(len(chosenside)+len(counterside))
        raNA = len(counterside)/(len(chosenside)+len(counterside))
        while (raAA != self.PARMRIGHT or raNA != self.PARMWRONG):
            self.add1toArm(chosen, choice, chosenalt, alt1, alt2, raAA)
            chosenside = []
            chosenside.extend(chosen)
            chosenside.extend(chosenalt)
            counterside = []
            counterside.extend(alt1)
            counterside.extend(alt2)
            raAA = len(chosenside) / (len(chosenside) + len(counterside))
            raNA = len(counterside) / (len(chosenside) + len(counterside))

    def add1toArm(self, chosen, choice, chosenalt, alt1, alt2, raAA):
        if (raAA <= self.PARMRIGHT):
            raCA = len(chosen) / (len(chosen) + len(chosenalt))
            self.add1toCat(chosen,choice, chosenalt, raCA)
        else:
            res = random.choice(list(range(2)))
            if (res == 0):
                add = random.choice(alt1)
                alt1.append(add)
            else:
                add = random.choice(alt2)
                alt2.append(add)




distr = Distributor()
distr.blanceImages(distr.array1,1)
distr.balanceCategories(distr.array1, distr.array2,1)
distr.balanceArms(distr.array1, 1, distr.array2,distr.array3, distr.array4)

print ("Array 1: " + str(distr.array1) + "Array 2: " + str(distr.array2) + "Array 3: " + str(distr.array3) +"Array 4: "  + str(distr.array4))
amtChoice = 0
for item in distr.array1:
    if item == 1:
        amtChoice += 1
        ratioCh = amtChoice / len(distr.array1)
print("Ratio inside Images for chosen: " + str (ratioCh) + " Ratio inside Images against chosen " + str(1-ratioCh))
raCA = len(distr.array1) / (len(distr.array1) + len(distr.array2))
print("Ratio inside Categories for chosen: " + str(raCA)+ " Ratio inside Categories against chosen: " + str(1-raCA))
chosenside = []
chosenside.extend(distr.array1)
chosenside.extend(distr.array2)
counterside = []
counterside.extend(distr.array3)
counterside.extend(distr.array4)
raAA = len(chosenside) / (len(chosenside) + len(counterside))
print("Ratio in Arms for Chosen: " + str(raAA) + " Ratio in Arms against Chosen: " + str(1-raAA))
print ("Total Accuracy for Truth: "+ str(raAA*raCA*ratioCh))

chosenside.extend(counterside)
acc = [0] * 12
print(chosenside)
for val in chosenside:
    acc[val] +=1
acc = [val / len(chosenside) for val in acc]
for i in range(len(acc)):
    print(f"{i}: Accumulation: {acc[i]:.3f}")

