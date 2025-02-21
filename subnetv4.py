#!/usr/bin/env python3
import sys
import math

def bitNot(n, numbits=8):
    return (1 << numbits) - 1 - n

def tryParseInt(value):
    try:
        return int(value)
    except ValueError:
        return None

def printBinary(value):
    print(format(value, "032b"))

def printDotNotation(value):
    bytes = [0, 0, 0, 0]
    val = value
    for i in range(3, -1, -1):
        bytes[i] = val & 0xff
        val >>= 8
    return "{}.{}.{}.{}".format(bytes[0], bytes[1], bytes[2], bytes[3])

#-b for binary output, -n forces the main network IP to be a valid NID.
printBinaryFlag = False
inputNIDFlag = False

mainNetworkStr = None
vlsmReqs = [] 
# The first non-flag argument is the main network.
# The remaining non-flag arguments are VLSM requirements.
args = sys.argv[1:]
for arg in args:
    if arg == "-b":
        printBinaryFlag = True
    elif arg == "-n":
        inputNIDFlag = True
    elif arg.startswith("-"):
        print("Invalid flag: " + arg)
        sys.exit(1)
    else:
        if mainNetworkStr is None:
            mainNetworkStr = arg
        else:
            req = tryParseInt(arg)
            if req is None or req < 1:
                print("Invalid VLSM requirement: " + arg)
                sys.exit(1)
            vlsmReqs.append(req)

if mainNetworkStr is None:
    print("No main network provided.\nUsage: python script.py [-b] [-n] <main_network> [vlsm_req1] [vlsm_req2] ...")
    sys.exit(1)

# Parse main network (expected format: IP/NETMASK, delimiter can be '/' or '\')
if "/" in mainNetworkStr:
    parts = mainNetworkStr.split("/")
elif "\\" in mainNetworkStr:
    parts = mainNetworkStr.split("\\")
else:
    print("Invalid main network format. Use IP/NETMASK")
    sys.exit(1)

if len(parts) != 2:
    print("Invalid main network format. Use IP/NETMASK")
    sys.exit(1)

ipAddressStr, netmaskBitsStr = parts
netmaskBits = tryParseInt(netmaskBitsStr)
if netmaskBits is None or netmaskBits < 1 or netmaskBits > 32:
    print("Invalid netmask bits in main network")
    sys.exit(1)

netmask = (1 << netmaskBits) - 1
netmask <<= (32 - netmaskBits)

ipParts = ipAddressStr.split(".")
if len(ipParts) != 4:
    print("Invalid IP address format in main network")
    sys.exit(1)

ipAddress = 0
for part in ipParts:
    byteVal = tryParseInt(part)
    if byteVal is None or byteVal < 0 or byteVal > 255:
        print("Invalid IP address part in main network")
        sys.exit(1)
    ipAddress = (ipAddress << 8) | byteVal

calculatedNID = ipAddress & netmask
if inputNIDFlag:
    
    if ipAddress != calculatedNID:
        print("Error: Provided main network IP is not a valid NID for the given netmask.")
        print("Provided:", printDotNotation(ipAddress), "should be", printDotNotation(calculatedNID))
        sys.exit(1)
    netAddress = ipAddress
else:
    netAddress = calculatedNID

mainBroadcast = netAddress | bitNot(netmask, 32)
mainTotal = 2 ** (32 - netmaskBits)
mainUsable = mainTotal - 2

# Print main network info
print("\nMain Network:")
print("IP:        ", printDotNotation(ipAddress))
print("SNM:       ", printDotNotation(netmask))
print("NID:       ", printDotNotation(netAddress))
print("FIP:       ", printDotNotation(netAddress + 1))
print("LIP:       ", printDotNotation(mainBroadcast - 1))
print("BR:        ", printDotNotation(mainBroadcast))
print("TNoH:      ", mainTotal)
print("TNoUH:     ", mainUsable)
if printBinaryFlag:
    print("\nBinary Representations:")
    print("IP:        ", end=""); printBinary(ipAddress)
    print("SNM:       ", end=""); printBinary(netmask)
    print("NID:       ", end=""); printBinary(netAddress)
    print("BR:        ", end=""); printBinary(mainBroadcast)

if not vlsmReqs:
    sys.exit(0)

# Sort VLSM requirements in descending order
vlsmReqs.sort(reverse=True)

def requiredSubnetSize(req):
    total = req + 2
    return 2 ** math.ceil(math.log2(total))

# VLSM allocation:
currentPointer = netAddress
subnetAllocations = []

for req in vlsmReqs:
    blockSize = requiredSubnetSize(req)
    allocatedMaskBits = 32 - int(math.log2(blockSize))
    allocatedMask = (1 << allocatedMaskBits) - 1
    allocatedMask <<= (32 - allocatedMaskBits)
    
    # Align currentPointer to the blockSize boundary relative to the main network.
    remainder = (currentPointer - netAddress) % blockSize
    if remainder != 0:
        currentPointer += (blockSize - remainder)
    
    allocatedNID = currentPointer
    allocatedBroadcast = allocatedNID + blockSize - 1
    allocatedFIP = allocatedNID + 1
    allocatedLIP = allocatedBroadcast - 1
    allocatedTotal = blockSize
    allocatedUsable = blockSize - 2
    
    # Check if the allocated block fits in the main network
    if allocatedBroadcast > mainBroadcast:
        print("Error: Not enough space in the main network for requirement:", req)
        sys.exit(1)
    
    subnetAllocations.append({
        'req': req,
        'NID': allocatedNID,
        'SNM': allocatedMask,
        'FIP': allocatedFIP,
        'LIP': allocatedLIP,
        'BR': allocatedBroadcast,
        'TNoH': allocatedTotal,
        'TNoUH': allocatedUsable,
        'maskBits': allocatedMaskBits
    })
    
    currentPointer = allocatedBroadcast + 1

print("\nVLSM Allocations:")
for alloc in subnetAllocations:
    print("\nFor requirement (usable hosts):", alloc['req'])
    print("NIDF:   ", printDotNotation(alloc['NID']))
    print("SNM:    ", printDotNotation(alloc['SNM']), " (/{} )".format(alloc['maskBits']))
    print("FIP:    ", printDotNotation(alloc['FIP']))
    print("LIP:    ", printDotNotation(alloc['LIP']))
    print("BR:     ", printDotNotation(alloc['BR']))
    print("TNoH:   ", alloc['TNoH'])
    print("TNoUH:  ", alloc['TNoUH'])
    if printBinaryFlag:
        print("Binary Representations:")
        print("NIDF:   ", end=""); printBinary(alloc['NID'])
        print("SNM:    ", end=""); printBinary(alloc['SNM'])
        print("BR:     ", end=""); printBinary(alloc['BR'])
