def run(protocol, experiment_dict, sample_volumes):
    """A function which uses a protocol object from the OT2 API V2 module which along with calculated and rearranged volumes will
    produce commands for the OT2. Additionally, information regarding the wells, slot and labware in use will be returned for use in information storage. Volume argument must be rearranged component wise (i.e. a total of n component lists should be fed). Volumes will be compared to available pipette's volume restriction and will be selected to optimize the number of commands. Returning of pipette tips is built in for when pipettes needs to be switched but will eventually switch back. """
    api_level = '2.0'
    
    metadata = {
    'protocolName': experiment_dict['Protocol Version'],
    'author': experiment_dict['Experimenter'],
    'description': experiment_dict['Project Tag'],
    'apiLevel': api_level}

    protocol.home()

    sample_plate = protocol.load_labware(experiment_dict['OT2 Sample Labware'], experiment_dict['OT2 Sample Labware Slot'])
    sample_plate_rows = [well for row in sample_plate.rows() for well in row] # allows for use of row ordering rather than default column ordering
    
    
    if len(sample_volumes)>len(sample_plate_rows):
        raise ValueError('Too many sample for single sample plate') 
    
#     for sample_volume in sample_volumes: # this might be better done outside of the script to better search for things it can still be done here but would be useful to use outside
#         if sum(sample_volume) > 
# def rearrange(sample_volumes):
#     """Rearranges sample information to group samples based on position in sublist. [[a1,b1,c1],[a2,b2,c2]] => [[a1,a2],[b1,b2],[c1,c2]]"""
#     component_volumes_rearranged = []
#     for i in range(len(sample_volumes[0])): 
#         component_volumes = []
#         for sample in sample_volumes:
#             component_volume = sample[i]
#             component_volumes.append(component_volume)
#         component_volumes_rearranged.append(component_volumes)
#     return component_volumes_rearranged 
    

           
    component_volume_lists = []    
    for i in range(len(sample_volumes[0])): 
        component_volumes = []
        for sample in sample_volumes:
            component_volume = sample[i]
            component_volumes.append(component_volume)
        component_volume_lists.append(component_volumes)
    
    print(len(component_volume_lists))
    
    stock_plate = protocol.load_labware(experiment_dict['OT2 Stock Labware'], experiment_dict['OT2 Stock Labware Slot'])
    stock_plate_rows = [well for row in stock_plate.rows() for well in row]
    
    right_tiprack = protocol.load_labware(experiment_dict['OT2 Right Tiprack'], experiment_dict['OT2 Right Tiprack Slot'])     
    right_pipette = protocol.load_instrument(experiment_dict['OT2 Right Pipette'], 'right', tip_racks = [right_tiprack])    
    right_pipette.well_bottom_clearance.dispense = experiment_dict['OT2 Bottom Clearance (mm)'] 

    left_tiprack = protocol.load_labware(experiment_dict['OT2 Left Tiprack'], experiment_dict['OT2 Left Tiprack Slot']) 
    left_pipette = protocol.load_instrument(experiment_dict['OT2 Left Pipette'], 'left', tip_racks = [left_tiprack])
    left_pipette.well_bottom_clearance.dispense = experiment_dict['OT2 Bottom Clearance (mm)']

    pipette_1 = right_pipette # the number one slot is always reserved for the volume limited case
    tiprack_1 = right_tiprack                          
    pipette_2 = left_pipette
    tiprack_2 = left_tiprack
    
    tiprack_1_rows = [well for row in tiprack_1.rows() for well in row]
    tiprack_2_rows = [well for row in tiprack_2.rows() for well in row]
  
    info_list = []
    for stock_index, component_volume_list in enumerate(component_volume_lists): 
        if component_volume_list[0] <= pipette_1.max_volume: #initializing pipette with tip for a component
            pipette = pipette_1
            pipette.pick_up_tip(tiprack_1_rows[stock_index])

        elif component_volume_list[0] > pipette_1.max_volume: #initializing pipette with tip for a component
            pipette = pipette_2
            pipette.pick_up_tip(tiprack_2_rows[stock_index])

        for well_index, volume in enumerate(component_volume_list):
            info = sample_plate_rows[well_index]
            info_list.append(info)
            if volume<pipette_1.max_volume and pipette == pipette_1:
                pipette.transfer(volume, stock_plate_rows[stock_index], sample_plate_rows[well_index], new_tip = 'never') 

            elif volume>pipette_1.max_volume and pipette == pipette_2:
                pipette.transfer(volume, stock_plate_rows[stock_index], sample_plate_rows[well_index], new_tip = 'never')

            elif volume<pipette_1.max_volume and pipette == pipette_2:
                pipette.return_tip()
                pipette = pipette_1
                pipette.pick_up_tip(tiprack_1_rows[stock_index])
                pipette.transfer(volume, stock_plate_rows[stock_index], sample_plate_rows[well_index], new_tip = 'never')

            elif volume>pipette_1.max_volume and pipette == pipette_1: 
                pipette.return_tip()
                pipette = pipette_2
                pipette.pick_up_tip(tiprack_2_rows[stock_index])
                pipette.transfer(volume, stock_plate_rows[stock_index], sample_plate_rows[well_index], new_tip = 'never')
        pipette.drop_tip()
#     final_well = [stock_plate_rows[stock_index], sample_plate_rows[well_index]]
    
    for line in protocol.commands():
        print(line)
    return info_list