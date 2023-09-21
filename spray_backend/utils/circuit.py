def get_circuit_list_data(circuits, boulder_id=None):
    DATA = []
    for circuit in circuits:
        boulder_is_in_circuit = circuit.boulders.filter(pk=boulder_id).exists()
        DATA.append({
            'id': circuit.id,
            'name': circuit.name,
            'description': circuit.description,
            'color': circuit.color,
            'private': circuit.private,
            'isSelected': boulder_is_in_circuit
        })
    return DATA