import 'package:flutter/material.dart';


void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: Scaffold(
          appBar: AppBar(
            backgroundColor: Colors.green,
            title: const Text("Palanquin"),
          ),
          body: Container(
            child: const Text("Testing"),
            margin: const EdgeInsets.all(50),
            padding: const EdgeInsets.all(10),
            color: Colors.red,
            height: 10,
            width: 10,
          ),
      )
    );
  }
}