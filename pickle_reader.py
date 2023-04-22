import dill

infile = "2205749221288812829/lap20.pkl"
with open(infile, 'rb') as in_strm:
    packets = dill.load(in_strm)
    print(f'Num packets: {len(packets)}')
    for packet in packets:
        if (packet.header.packet_id == 6): #PacketCarTelemetryData
            session_time = packet.header.session_time
            speed = packet.car_telemetry_data[0].speed
            throttle = packet.car_telemetry_data[0].throttle
            brake = packet.car_telemetry_data[0].brake
            drs = packet.car_telemetry_data[0].drs

            print(f'Speed: {speed}KPH, Throttle: {throttle*100:0.0f}%, Brake: {brake*100:0.0f}%')

