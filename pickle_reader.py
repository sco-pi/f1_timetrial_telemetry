import dill
import json
import gzip

compress_output = True

session = "2589074988933037945"
lap     = "8"

infile_name  = f"{session}/lap{lap}.pkl"
outfile_name = f"{session}/lap{lap}.json"

sorted_packets = {
    "PacketMotionData": [],
    "PacketSessionData": [],
    "PacketLapData": [],
    "PacketEventData": [],
    "PacketParticipantsData": [],
    "PacketCarSetupData": [],
    "PacketCarTelemetryData": [],
    "PacketCarTelemetryData": [],
    "PacketCarStatusData": [],
    "PacketFinalClassificationData": [],
    "PacketLobbyInfoData": [],
    "PacketCarDamageData": [],
    "PacketSessionHistoryData": []
}

with open(infile_name, 'rb') as infile:
    packets = dill.load(infile)
    print(f'Num packets: {len(packets)}')
    for packet in packets:
        if (packet.header.packet_id == 0): #PacketMotionData
            sorted_packets["PacketMotionData"].append(packet.to_dict())
        elif (packet.header.packet_id == 1): #PacketSessionData
            sorted_packets["PacketSessionData"].append(packet.to_dict())
        elif (packet.header.packet_id == 2): #PacketLapData
            sorted_packets["PacketLapData"].append(packet.to_dict())
        elif (packet.header.packet_id == 3): #PacketEventData
            sorted_packets["PacketEventData"].append(packet.to_dict())
        elif (packet.header.packet_id == 4): #PacketParticipantsData
            sorted_packets["PacketParticipantsData"].append(packet.to_dict())
        elif (packet.header.packet_id == 5): #PacketCarSetupData
            sorted_packets["PacketCarSetupData"].append(packet.to_dict())
        elif (packet.header.packet_id == 6): #PacketCarTelemetryData
            sorted_packets["PacketCarTelemetryData"].append(packet.to_dict())

            #session_time = packet.header.session_time
            #speed = packet.car_telemetry_data[0].speed
            #throttle = packet.car_telemetry_data[0].throttle
            #brake = packet.car_telemetry_data[0].brake
            #drs = packet.car_telemetry_data[0].drs
            #
            #print(f'Speed: {speed}KPH, Throttle: {throttle*100:0.0f}%, Brake: {brake*100:0.0f}%')
        elif (packet.header.packet_id == 7): #PacketCarStatusData
            sorted_packets["PacketCarStatusData"].append(packet.to_dict())
        elif (packet.header.packet_id == 8): #PacketFinalClassificationData
            sorted_packets["PacketFinalClassificationData"].append(packet.to_dict())
        elif (packet.header.packet_id == 9): #PacketLobbyInfoData
            sorted_packets["PacketLobbyInfoData"].append(packet.to_dict())
        elif (packet.header.packet_id == 10): #PacketCarDamageData
            sorted_packets["PacketCarDamageData"].append(packet.to_dict())
        elif (packet.header.packet_id == 11): #PacketSessionHistoryData
            sorted_packets["PacketSessionHistoryData"].append(packet.to_dict())

    if compress_output:
        with gzip.open(f'{outfile_name}.gz', 'wt') as outfile:
            #outfile.write(json.dumps(sorted_packets, indent=2))
            json.dump(sorted_packets, outfile)
    else:
        with open(outfile_name, 'w') as outfile:
            json.dump(sorted_packets, outfile)

#print(json.dumps(sorted_packets, indent=2))
