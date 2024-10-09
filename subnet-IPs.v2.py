
import sys

# helper functions

def bitNot(n, numbits=8):
    return (1 << numbits) - 1 - n

def printErrorAndExit(str = ""):
    print("Invalid input '" + str + "' ")
    print("Usage: subnet262 [{ip-addres}/{netmask bit count}]")
    exit(1)

def tryParseInt(value):
    try:
        return int(value)
    except ValueError:
        return None

def printBinary(value):
    print(format(value, "032b"), end="")

def printDotNotaion(value):
    bytes = [0, 0, 0, 0]
    val = value
    for i in range(3, -1, -1):
        bytes[i] = val & 0xff
        val >>= 8
    print("{0}.{1}.{2}.{3}".format(bytes[0], bytes[1], bytes[2], bytes[3]), end="")
        
# get input from command line, or ask for user input

inputStr = ""

if (len(sys.argv) == 1):
    inputStr = input("Enter IP address with netmask bit count: ")
elif (len(sys.argv) == 2):
    inputStr = sys.argv[1]
else:
    printErrorAndExit()

# split input to IP address and netmask bit count

ipAddressStr = ""    
netmaskBitsStr = ""

split1 = inputStr.split("/")
if (len(split1) != 2):
    printErrorAndExit(inputStr)
ipAddressStr = split1[0]
netmaskBitsStr = split1[1]

# calculate 32 bit netmask

netmaskBits = tryParseInt(netmaskBitsStr)
if (netmaskBits == None or netmaskBits < 1 or netmaskBits > 32):
    printErrorAndExit(inputStr)
netmask = (1 << netmaskBits) -1
netmask <<= (32 - netmaskBits)

# calculate 32 bit IP address

ipAddressParts = ipAddressStr.split(".")
if (len(ipAddressParts) != 4):
    printErrorAndExit(inputStr)

ipAddress = 0
for b in ipAddressParts:
    ipAddressByte = tryParseInt(b)
    if (ipAddressByte == None or ipAddressByte < 0 or ipAddressByte > 255):
        printErrorAndExit(inputStr)
    ipAddress <<= 8
    ipAddress |= ipAddressByte

# print results
print("")
print("IP Address       ", end="")
printBinary(ipAddress)
print(" ", end="")
printDotNotaion(ipAddress)
print()

print("NetMask          ", end="")
printBinary(netmask)
print(" ", end="")
printDotNotaion(netmask)
print()

netAddress = ipAddress & netmask
print("NetAddress       ", end="")
printBinary(netAddress)
print(" ", end="")
printDotNotaion(netAddress)
print()

broadcastAddress = netAddress | bitNot(netmask, 32)
print("BroadcastAddress ", end="")
printBinary(broadcastAddress)
print(" ", end="")
printDotNotaion(broadcastAddress)
print()

print("")
firstAddress = netAddress +1
print("First Usable IP ", end="")
print(" ", end="")
printDotNotaion(firstAddress)
print()
lastAddress= broadcastAddress -1
print("Last usable IP:  ", end="")
printDotNotaion(lastAddress)
print("")

totalHosts=2**(32- netmaskBits)
print("Total Hosts  :   " ,end="")
print(totalHosts)
totalUsable= totalHosts -2
print("Usable Hosts :   " ,end="")
print(totalUsable)