                if act["action"] == "generate_sample":
                    await manager.broadcast(json.dumps({"type": "STATUS", "msg": "🎨 COMPOSING SAMPLE..."}))
                    await manager.broadcast(json.dumps({"type": "PROGRESS", "val": 20}))
                    
                    result = await asyncio.to_thread(
                        generate_sample, 
                        prompt=act["prompt"], 
                        key=current_key,
                        bpm=current_bpm,
                        engine=command.sampleEngine,
                        api_key=command.geminiKey
                    )
                    
                    if result.get("status") == "success":
                        await manager.broadcast(json.dumps({"type": "PROGRESS", "val": 100}))
                        await manager.broadcast(json.dumps({
                            "type": "SAMPLE_GENERATED", 
                            "file": result["file"],
                            "prompt": act["prompt"]
                        }))
                        await manager.broadcast(json.dumps({"type": "STATUS", "msg": "✨ SAMPLE READY!"}))
                        results.append(result)
                    else:
                        await manager.broadcast(json.dumps({"type": "PROGRESS", "val": 0}))
                        await manager.broadcast(json.dumps({"type": "STATUS", "msg": f"❌ FAILED: {result.get('error')}"}))
                        results.append(result)

                elif act["action"] == "generate_midi":
                    await manager.broadcast(json.dumps({"type": "STATUS", "msg": "🎹 WRITING MIDI..."}))
                    await manager.broadcast(json.dumps({"type": "PROGRESS", "val": 30}))
                    
                    from orchestration.midi_engine import generate_midi
                    result = await asyncio.to_thread(
                        generate_midi,
                        prompt=act["prompt"],
                        key=current_key,
                        bpm=current_bpm,
                        engine=command.midiEngine,
                        api_key=command.geminiKey
                    )
                    
                    if result.get("status") == "success":
                        await manager.broadcast(json.dumps({"type": "PROGRESS", "val": 100}))
                        await manager.broadcast(json.dumps({
                            "type": "MIDI_READY",
                            "file": result["file"],
                            "prompt": act["prompt"]
                        }))
                        await manager.broadcast(json.dumps({"type": "STATUS", "msg": "✅ MIDI READY!"}))
                        results.append(result)
                    else:
                        await manager.broadcast(json.dumps({"type": "PROGRESS", "val": 0}))
                        await manager.broadcast(json.dumps({"type": "STATUS", "msg": f"❌ FAILED: {result.get('error')}"}))
                        results.append(result)
